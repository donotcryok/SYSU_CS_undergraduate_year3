/**
 * parallel_for.c — 基于 Pthreads 线程池的 parallel_for 实现
 */

#define _POSIX_C_SOURCE 200809L

#include "parallel_for.h"
#include <pthread.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdatomic.h>

/* ------------------------------------------------------------------ */
/*  内部类型定义                                                       */
/* ------------------------------------------------------------------ */

/** 任务描述：每次 parallel_for 调用时由主线程填充 */
typedef struct {
    int    start;       /* 迭代起始（含） */
    int    end;         /* 迭代结束（不含） */
    int    inc;         /* 步长 */
    int    num_threads; /* 当前工作线程数 */
    int    total_iters; /* 总迭代次数 = ceil((end-start)/inc) */

    /* Static scheduling */
    int    base_chunk;  /* 基本块大小 */
    int    remainder;   /* 残差迭代数 */

    /* Dynamic scheduling */
    atomic_int next_iter; /* 下一个待分配的迭代索引 (0-based in [0, total_iters)) */

    pf_schedule_t schedule; /* 调度策略 */

    void *(*functor)(int, void*); /* 用户函数 */
    void *arg;                    /* 用户参数 */
} task_desc_t;

/** 线程池上下文 */
typedef struct {
    pthread_mutex_t mutex;        /* 保护以下所有字段 + 主线程/工作线程同步 */
    pthread_cond_t  worker_cv;    /* 工作线程等待任务 */
    pthread_cond_t  main_cv;      /* 主线程等待完成 */

    pthread_t      *threads;      /* 工作线程数组 */
    int             num_threads;  /* 当前线程池大小 */
    volatile int    running;      /* 新任务已分派标志 */
    volatile int    shutdown;     /* 是否请求销毁线程池 */

    task_desc_t     task;         /* 当前任务描述 */
    volatile int    counter;      /* 已完成的工作线程计数 */
    volatile int    epoch;        /* 任务纪元（每次 parallel_for 递增） */
} thread_pool_t;

/* 线程局部存储键（用于 parallel_for_get_tid） */
static pthread_key_t  tid_key;
static pthread_once_t tid_key_once = PTHREAD_ONCE_INIT;

/* 全局线程池实例 */
static thread_pool_t  g_pool = {
    PTHREAD_MUTEX_INITIALIZER,
    PTHREAD_COND_INITIALIZER,
    PTHREAD_COND_INITIALIZER,
    NULL, 0, 0, 0,
    {0, 0, 1, 0, 0, 0, 0, ATOMIC_VAR_INIT(0), 0, NULL, NULL},
    0, 0
};
static pthread_once_t g_pool_init_once = PTHREAD_ONCE_INIT;

/* ------------------------------------------------------------------ */
/*  内部辅助函数                                                       */
/* ------------------------------------------------------------------ */

/** 计算总迭代次数 (向上取整) */
static inline int calc_total_iters(int start, int end, int inc)
{
    int range = end - start;
    if (range <= 0) return 0;
    return (range + inc - 1) / inc;
}

/** 由 0-based 逻辑迭代索引计算真实循环变量 */
static inline int iter_to_idx(int logical_iter, int start, int inc)
{
    return start + logical_iter * inc;
}

/** 初始化线程局部存储键 */
static void make_tid_key(void)
{
    pthread_key_create(&tid_key, NULL);
}

/* 前向声明 */
static void pool_destroy(void);

/* ------------------------------------------------------------------ */
/*  调度策略执行函数                                                    */
/* ------------------------------------------------------------------ */

/**
 * 执行静态块调度 (Block Scheduling)
 *   base_chunk = total_iters / T
 *   remainder  = total_iters % T
 *   前 remainder 个线程各多处理 1 个迭代
 */
static void exec_static(const task_desc_t *t, int tid)
{
    int chunk = t->base_chunk + (tid < t->remainder ? 1 : 0);
    if (chunk <= 0) return;

    int offset = 0;
    for (int k = 0; k < tid; k++) {
        offset += t->base_chunk + (k < t->remainder ? 1 : 0);
    }

    int iter_end = offset + chunk;
    for (int li = offset; li < iter_end; li++) {
        t->functor(iter_to_idx(li, t->start, t->inc), t->arg);
    }
}

/**
 * 执行轮询调度 (Cyclic Scheduling)
 *   迭代 i 分配给线程 (i-start)/inc % T
 */
static void exec_cyclic(const task_desc_t *t, int tid)
{
    int T = t->num_threads;
    for (int li = tid; li < t->total_iters; li += T) {
        t->functor(iter_to_idx(li, t->start, t->inc), t->arg);
    }
}

/**
 * 执行动态调度 (Dynamic Scheduling)
 *   原子自增计数器，每线程每次取 1 个迭代
 */
static void exec_dynamic(const task_desc_t *t, int tid)
{
    (void)tid;
    int total = t->total_iters;
    while (1) {
        /* 通过强制转换为 volatile 指针避免 const 警告 */
        int li = atomic_fetch_add((atomic_int *)&t->next_iter, 1);
        if (li >= total) break;
        t->functor(iter_to_idx(li, t->start, t->inc), t->arg);
    }
}

/* ------------------------------------------------------------------ */
/*  工作线程主循环                                                     */
/* ------------------------------------------------------------------ */

static void *worker_loop(void *arg)
{
    int tid = (int)(intptr_t)arg;
    int my_epoch = 0;  /* 本线程已处理的任务纪元 */

    /* tid+1 避免 tid==0 时 pthread_setspecific 存入 NULL */
    pthread_setspecific(tid_key, (void *)(intptr_t)(tid + 1));
    pthread_mutex_lock(&g_pool.mutex);

    while (1) {
        /*
         * 等待新任务：running == 0 或 epoch 未变化时休眠。
         * 条件：无新任务 且 非 shutdown → wait
         */
        while ((g_pool.running == 0 || g_pool.epoch == my_epoch)
               && !g_pool.shutdown) {
            pthread_cond_wait(&g_pool.worker_cv, &g_pool.mutex);
        }

        /* 线程池销毁请求 */
        if (g_pool.shutdown) {
            pthread_mutex_unlock(&g_pool.mutex);
            return NULL;
        }

        /* 记录新 epoch，拷贝任务描述（持锁期间安全读取） */
        my_epoch = g_pool.epoch;
        task_desc_t t = g_pool.task;
        pthread_mutex_unlock(&g_pool.mutex);

        /* ---- 无锁执行区：按调度策略执行 ---- */
        switch (t.schedule) {
        case PF_SCHED_STATIC:
            exec_static(&t, tid);
            break;
        case PF_SCHED_CYCLIC:
            exec_cyclic(&t, tid);
            break;
        case PF_SCHED_DYNAMIC:
            exec_dynamic(&t, tid);
            break;
        default:
            exec_static(&t, tid);
            break;
        }

        /* ---- 重新持锁，报告完成 ---- */
        pthread_mutex_lock(&g_pool.mutex);
        g_pool.counter++;

        /*
         * 最后一个完成的线程唤醒主线程。
         */
        if (g_pool.counter == t.num_threads) {
            pthread_cond_signal(&g_pool.main_cv);
        }
    }
    /* unreachable */
}

/* ------------------------------------------------------------------ */
/*  线程池生命周期管理                                                 */
/* ------------------------------------------------------------------ */

/** 线程池初始化（pthread_once 回调，实际为 no-op） */
static void pool_init_once(void)
{
    /* lazy init — 第一次 parallel_for 调用时由 pool_create 完成 */
}

/** 创建线程池 */
static void pool_create(int num_threads)
{
    if (g_pool.threads != NULL) {
        pool_destroy();
    }

    g_pool.num_threads = num_threads;
    g_pool.threads     = (pthread_t *)malloc(
                            (size_t)num_threads * sizeof(pthread_t));
    g_pool.running     = 0;
    g_pool.shutdown    = 0;
    g_pool.counter     = 0;
    g_pool.epoch       = 0;

    if (g_pool.threads == NULL) {
        fprintf(stderr, "parallel_for: malloc failed for thread array\n");
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < num_threads; i++) {
        int ret = pthread_create(&g_pool.threads[i], NULL, worker_loop,
                                 (void *)(intptr_t)i);
        if (ret != 0) {
            fprintf(stderr, "parallel_for: pthread_create failed "
                            "(err=%d)\n", ret);
            exit(EXIT_FAILURE);
        }
    }
}

/** 销毁线程池 */
static void pool_destroy(void)
{
    if (g_pool.threads == NULL) return;

    pthread_mutex_lock(&g_pool.mutex);
    g_pool.shutdown = 1;
    pthread_cond_broadcast(&g_pool.worker_cv);
    pthread_mutex_unlock(&g_pool.mutex);

    for (int i = 0; i < g_pool.num_threads; i++) {
        pthread_join(g_pool.threads[i], NULL);
    }

    free(g_pool.threads);
    g_pool.threads     = NULL;
    g_pool.num_threads = 0;
    g_pool.shutdown    = 0;
    g_pool.running     = 0;
}

/* ------------------------------------------------------------------ */
/*  核心调度逻辑（parallel_for 和 parallel_for_sched 共用）            */
/* ------------------------------------------------------------------ */

static void parallel_for_impl(int start, int end, int inc,
                              void *(*functor)(int, void*), void *arg,
                              int num_threads, pf_schedule_t schedule)
{
    /* 参数校验 */
    if (inc <= 0) return;
    if (start >= end) return;
    if (functor == NULL) return;

    /* 串行回退：0 或 1 线程时直接在当前线程执行 */
    if (num_threads <= 1) {
        pthread_once(&tid_key_once, make_tid_key);
        pthread_setspecific(tid_key, (void *)(intptr_t)1);  /* tid=0 */
        for (int i = start; i < end; i += inc) {
            functor(i, arg);
        }
        return;
    }

    /* 确保 tid_key 已初始化 */
    pthread_once(&tid_key_once, make_tid_key);

    /* 确保全局池已初始化 */
    pthread_once(&g_pool_init_once, pool_init_once);

    /* 如果线程数变化，重建线程池 */
    if (g_pool.threads == NULL || g_pool.num_threads != num_threads) {
        if (g_pool.threads != NULL) {
            pool_destroy();
        }
        pool_create(num_threads);
    }

    /* ---- 填充任务描述（持锁） ---- */
    pthread_mutex_lock(&g_pool.mutex);

    int total_iters = calc_total_iters(start, end, inc);

    g_pool.task.start       = start;
    g_pool.task.end         = end;
    g_pool.task.inc         = inc;
    g_pool.task.num_threads = num_threads;
    g_pool.task.total_iters = total_iters;
    g_pool.task.base_chunk  = total_iters / num_threads;
    g_pool.task.remainder   = total_iters % num_threads;
    g_pool.task.schedule    = schedule;
    g_pool.task.functor     = functor;
    g_pool.task.arg         = arg;

    /* Dynamic: 重置原子计数器 */
    atomic_store(&g_pool.task.next_iter, 0);

    g_pool.counter = 0;
    g_pool.epoch++;       /* 新纪元：所有工作线程的 my_epoch 均 < epoch */
    g_pool.running = 1;

    /* 唤醒所有工作线程 */
    pthread_cond_broadcast(&g_pool.worker_cv);

    /* 等待所有工作线程完成 */
    while (g_pool.counter < num_threads) {
        pthread_cond_wait(&g_pool.main_cv, &g_pool.mutex);
    }

    g_pool.running = 0;
    pthread_mutex_unlock(&g_pool.mutex);
}

/* ------------------------------------------------------------------ */
/*  公开 API                                                           */
/* ------------------------------------------------------------------ */

void parallel_for(int start, int end, int inc,
                  void *(*functor)(int, void*), void *arg,
                  int num_threads)
{
    parallel_for_impl(start, end, inc, functor, arg, num_threads,
                      PF_SCHED_STATIC);
}

void parallel_for_sched(int start, int end, int inc,
                        void *(*functor)(int, void*), void *arg,
                        int num_threads, pf_schedule_t schedule)
{
    parallel_for_impl(start, end, inc, functor, arg, num_threads,
                      schedule);
}

int parallel_for_get_tid(void)
{
    void *val = pthread_getspecific(tid_key);
    /* 主线程（未在工作线程中调用）返回 0 */
    if (val == NULL) return 0;
    return (int)(intptr_t)val - 1;
}

void parallel_for_cleanup(void)
{
    pool_destroy();
}
