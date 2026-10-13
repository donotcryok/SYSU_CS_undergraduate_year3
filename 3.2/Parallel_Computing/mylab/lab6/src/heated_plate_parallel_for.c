/**
 * heated_plate_parallel_for.c — 使用 parallel_for 库的热传导模拟
 * 调度策略通过命令行参数指定：
 *   ./heated_plate_parallel_for [M] [N] [epsilon] [num_threads] [schedule]
 *   schedule: static (0), cyclic (1), dynamic (2)
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "parallel_for.h"

/* ------------------------------------------------------------------ */
/*  全局状态（供 functor 访问）                                         */
/* ------------------------------------------------------------------ */

static int    g_M, g_N;
static double *g_u = NULL;
static double *g_w = NULL;

/* 差分归约：每个线程的局部最大 diff */
static double *g_local_diff = NULL;

/* ------------------------------------------------------------------ */
/*  functor 定义                                                       */
/* ------------------------------------------------------------------ */

/**
 * save_functor: 将 W 的一行保存到 U
 *   parallel_for(0, M, 1, save_functor, NULL, num_threads)
 */
static void *save_functor(int i, void *arg)
{
    (void)arg;
    int N = g_N;
    double *w = g_w;
    double *u = g_u;
    int base = i * N;
    for (int j = 0; j < N; j++) {
        u[base + j] = w[base + j];
    }
    return NULL;
}

/**
 * compute_functor: Jacobi 迭代 — 计算行 i 的新值
 *   parallel_for(1, M-1, 1, compute_functor, NULL, num_threads)
 */
static void *compute_functor(int i, void *arg)
{
    (void)arg;
    int N = g_N;
    double *u = g_u;
    double *w = g_w;

    int row_i      = i * N;
    int row_north  = (i - 1) * N;
    int row_south  = (i + 1) * N;

    for (int j = 1; j < N - 1; j++) {
        w[row_i + j] = (u[row_north + j] + u[row_south + j]
                      + u[row_i + j - 1] + u[row_i + j + 1]) * 0.25;
    }
    return NULL;
}

/**
 * diff_functor: 计算行 i 的局部最大差分，存入 g_local_diff[tid]
 *   parallel_for(1, M-1, 1, diff_functor, NULL, num_threads)
 */
static void *diff_functor(int i, void *arg)
{
    (void)arg;
    int N = g_N;
    double *u = g_u;
    double *w = g_w;
    int tid = parallel_for_get_tid();

    int base = i * N;
    double md = 0.0;
    for (int j = 1; j < N - 1; j++) {
        double d = fabs(w[base + j] - u[base + j]);
        if (d > md) md = d;
    }

    /* 更新线程局部最大差分（不需要锁，每个线程写独立槽位） */
    if (md > g_local_diff[tid]) {
        g_local_diff[tid] = md;
    }
    return NULL;
}

/* ------------------------------------------------------------------ */
/*  辅助函数                                                           */
/* ------------------------------------------------------------------ */

static double get_time_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static const char *schedule_name(pf_schedule_t s)
{
    switch (s) {
    case PF_SCHED_STATIC:  return "static";
    case PF_SCHED_CYCLIC:  return "cyclic";
    case PF_SCHED_DYNAMIC: return "dynamic";
    default:               return "unknown";
    }
}

/* ------------------------------------------------------------------ */
/*  主函数                                                             */
/* ------------------------------------------------------------------ */

int main(int argc, char *argv[])
{
    int          M           = (argc > 1) ? atoi(argv[1]) : 500;
    int          N           = (argc > 2) ? atoi(argv[2]) : 500;
    double       epsilon     = (argc > 3) ? atof(argv[3]) : 0.001;
    int          num_threads = (argc > 4) ? atoi(argv[4]) : 1;
    pf_schedule_t schedule   = (argc > 5) ? (pf_schedule_t)atoi(argv[5])
                                          : PF_SCHED_STATIC;

    if (M <= 0) M = 500;
    if (N <= 0) N = 500;
    if (epsilon <= 0.0) epsilon = 0.001;
    if (num_threads <= 0) num_threads = 1;

    g_M = M; g_N = N;

    printf("\nHEATED_PLATE_PARALLEL_FOR\n");
    printf("  Grid: %d x %d\n  Epsilon: %e\n", M, N, epsilon);
    printf("  Threads: %d\n  Schedule: %s\n", num_threads,
           schedule_name(schedule));

    /* ── 内存分配 ── */
    size_t ms = (size_t)M * N * sizeof(double);
    g_u = (double *)aligned_alloc(64, ms);
    g_w = (double *)aligned_alloc(64, ms);
    g_local_diff = (double *)calloc((size_t)num_threads, sizeof(double));

    if (!g_u || !g_w || !g_local_diff) {
        fprintf(stderr, "malloc failed\n");
        free(g_u); free(g_w); free(g_local_diff);
        return 1;
    }

    /* ── 边界条件初始化 ── */
    /* 注意：这里使用串行初始化，因为边界设置是轻量级操作 */
    for (int i = 1; i < M - 1; i++) {
        g_w[i * N + 0]      = 100.0;
        g_w[i * N + N - 1]  = 100.0;
    }
    for (int j = 0; j < N; j++) {
        g_w[0 * N + j]           = 0.0;
        g_w[(M - 1) * N + j]     = 100.0;
    }

    /* 计算边界均值 */
    double mean = 0.0;
    for (int i = 1; i < M - 1; i++)
        mean += g_w[i * N + 0] + g_w[i * N + N - 1];
    for (int j = 0; j < N; j++)
        mean += g_w[0 * N + j] + g_w[(M - 1) * N + j];
    mean /= (double)(2 * M + 2 * N - 4);
    printf("  MEAN = %f\n", mean);

    /* 内部初始化 */
    for (int i = 1; i < M - 1; i++)
        for (int j = 1; j < N - 1; j++)
            g_w[i * N + j] = mean;

    /* ── 迭代主循环 ── */
    double diff = epsilon;
    int iterations = 0, iterations_print = 1;

    printf("\n Iteration  Change\n\n");
    fflush(stdout);

    double t_start = get_time_sec();

    while (epsilon <= diff) {
        /*
         * Phase A: 保存旧解 U ← W
         * parallel_for 将行 [0, M) 按指定调度策略分配给线程
         */
        parallel_for_sched(0, M, 1, save_functor, NULL,
                           num_threads, schedule);

        /*
         * Phase B: Jacobi 更新 — 仅内部点 [1, M-1)
         */
        parallel_for_sched(1, M - 1, 1, compute_functor, NULL,
                           num_threads, schedule);

        /*
         * Phase C: 计算差分
         */
        memset(g_local_diff, 0, (size_t)num_threads * sizeof(double));
        parallel_for_sched(1, M - 1, 1, diff_functor, NULL,
                           num_threads, schedule);

        /* 归约：取所有线程的最大局部 diff */
        diff = 0.0;
        for (int t = 0; t < num_threads; t++) {
            if (g_local_diff[t] > diff) diff = g_local_diff[t];
        }

        iterations++;
        if (iterations == iterations_print) {
            printf("  %8d  %f\n", iterations, diff);
            fflush(stdout);
            iterations_print *= 2;
        }
    }

    double wtime = get_time_sec() - t_start;

    printf("\n  %8d  %f\n", iterations, diff);
    printf("\n  Error tolerance achieved.\n");
    printf("  Wallclock time = %f\n", wtime);
    printf("\nHEATED_PLATE_PARALLEL_FOR: Normal end of execution.\n");

    /* CSV 输出 */
    fprintf(stderr, "CSV,%d,%d,%e,%d,%s,%f\n",
            M, N, epsilon, num_threads, schedule_name(schedule), wtime);

    /* ── 清理 ── */
    free(g_u);
    free(g_w);
    free(g_local_diff);
    parallel_for_cleanup();

    return 0;
}
