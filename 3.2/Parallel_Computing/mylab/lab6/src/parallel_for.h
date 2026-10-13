#ifndef PARALLEL_FOR_H
#define PARALLEL_FOR_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 调度策略枚举（模仿 OpenMP 的 schedule 子句）
 */
typedef enum {
    PF_SCHED_STATIC  = 0,  /**< 静态块分配 (Block Scheduling)，默认策略 */
    PF_SCHED_CYCLIC  = 1,  /**< 轮询分配 (Cyclic / round-robin) */
    PF_SCHED_DYNAMIC = 2,  /**< 动态分配 (Dynamic)，每线程每次取 1 个迭代 */
} pf_schedule_t;

/**
 * @brief 并行 for 循环（默认 static block scheduling）
 *
 * 等价于 parallel_for_sched(start, end, inc, functor, arg,
 *                           num_threads, PF_SCHED_STATIC)。
 */
void parallel_for(int start, int end, int inc,
                  void *(*functor)(int, void*), void *arg,
                  int num_threads);

/**
 * @brief 带调度策略的并行 for 循环
 *
 * 将区间 [start, end) 以步长 inc、按 schedule 策略分配给
 * num_threads 个线程，每个线程调用 functor(i, arg)。
 *
 * @param start       迭代起始索引（含）
 * @param end         迭代结束索引（不含），半开区间
 * @param inc         迭代步长，必须 > 0
 * @param functor     函数指针，签名为 void* f(int iteration_index, void *arg)
 * @param arg         传递给 functor 的共享参数指针
 * @param num_threads 请求的线程数；若 <= 1 则串行执行
 * @param schedule    调度策略 (PF_SCHED_STATIC / PF_SCHED_CYCLIC / PF_SCHED_DYNAMIC)
 */
void parallel_for_sched(int start, int end, int inc,
                        void *(*functor)(int, void*), void *arg,
                        int num_threads, pf_schedule_t schedule);

/**
 * @brief 获取调用线程在 parallel_for 线程池中的 ID (0-based)
 *
 * 仅在 parallel_for / parallel_for_sched 的 functor 回调内部调用时有意义，
 * 其他上下文返回 0。
 */
int parallel_for_get_tid(void);

/**
 * @brief 销毁 parallel_for 内部的线程池，释放资源
 *
 * 通常在程序退出前调用，确保所有工作线程正确终止。
 */
void parallel_for_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* PARALLEL_FOR_H */
