/**
 * 策略说明:
 *   0 (Global Mutex): 逐元素加锁 - 每次累加都加锁，严重锁竞争
 *   1 (Local Reduction): 局部归约 - 仅最后加锁一次，高效并行
 */

#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

// 策略常量
#define STRATEGY_GLOBAL_MUTEX   0
#define STRATEGY_LOCAL_REDUCTION 1

// 策略名称
const char* strategy_names[] = {"Global-Mutex", "Local-Reduction"};

// 全局变量
long long *array = NULL;           // 全局数组
long long global_sum = 0;          // 全局求和结果
long long array_size = 0;          // 数组大小
int num_threads = 0;               // 线程数
int strategy = 0;                  // 当前策略
pthread_mutex_t sum_mutex;         // 互斥锁

// 线程参数结构体
typedef struct {
    int thread_id;         // 线程ID
    long long start_idx;   // 起始索引
    long long end_idx;     // 结束索引（不包含）
    long long local_sum;   // 局部求和结果（仅用于Local Reduction）
} ThreadArg;

// 获取当前时间（秒）
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

// 策略0：逐元素加锁（Global Mutex）- 性能灾难
void* sum_thread_global_mutex(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    // 逐元素加锁：每次累加都要竞争锁
    // 这会导致严重的锁竞争，多线程性能可能比单线程更差
    for (long long i = params->start_idx; i < params->end_idx; i++) {
        pthread_mutex_lock(&sum_mutex);
        global_sum += array[i];
        pthread_mutex_unlock(&sum_mutex);
    }
    
    pthread_exit(NULL);
    return NULL;
}

// 策略1：局部归约（Local Reduction）- 高效并行
void* sum_thread_local_reduction(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    // 局部归约：每个线程维护自己的局部和
    // 在循环累加过程中完全不使用锁
    long long local_sum = 0;
    
    for (long long i = params->start_idx; i < params->end_idx; i++) {
        local_sum += array[i];  // 无锁累加，完全并行
    }
    
    // 仅在最后一次性加锁
    // 锁操作次数从 O(n) 降低到 O(num_threads)
    pthread_mutex_lock(&sum_mutex);
    global_sum += local_sum;
    pthread_mutex_unlock(&sum_mutex);
    
    pthread_exit(NULL);
    return NULL;
}

// 线程函数入口 - 根据策略选择不同实现
void* sum_thread(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    switch (strategy) {
        case STRATEGY_GLOBAL_MUTEX:
            return sum_thread_global_mutex(arg);
        case STRATEGY_LOCAL_REDUCTION:
            return sum_thread_local_reduction(arg);
        default:
            return sum_thread_local_reduction(arg);
    }
}

int main(int argc, char *argv[]) {
    // 参数检查
    if (argc != 4) {
        fprintf(stderr, "Usage: %s array_size num_threads strategy\n", argv[0]);
        fprintf(stderr, "  array_size: size of array (e.g., 1000000 for 1M)\n");
        fprintf(stderr, "  num_threads: number of threads (1-16)\n");
        fprintf(stderr, "  strategy: 0=Global-Mutex, 1=Local-Reduction (default=1)\n");
        return 1;
    }
    
    // 解析命令行参数
    array_size = atoll(argv[1]);
    num_threads = atoi(argv[2]);
    strategy = atoi(argv[3]);
    
    // 参数有效性检查
    if (array_size <= 0) {
        fprintf(stderr, "Error: Array size must be a positive integer\n");
        return 1;
    }
    if (num_threads < 1 || num_threads > 16) {
        fprintf(stderr, "Error: Number of threads must be between 1 and 16\n");
        return 1;
    }
    if (strategy < 0 || strategy > 1) {
        fprintf(stderr, "Error: Strategy must be 0 or 1\n");
        return 1;
    }
    
    // 动态分配数组
    array = (long long *)malloc(array_size * sizeof(long long));
    if (!array) {
        fprintf(stderr, "Error: Memory allocation failed for array\n");
        return 1;
    }
    
    // 初始化随机数组（使用固定种子保证可重复性）
    srand(42);
    for (long long i = 0; i < array_size; i++) {
        // 生成 0-99 的随机数
        array[i] = rand() % 100;
    }
    
    // 初始化互斥锁
    pthread_mutex_init(&sum_mutex, NULL);
    
    // 重置全局和
    global_sum = 0;
    
    // 创建线程和参数数组
    pthread_t *threads = (pthread_t *)malloc(num_threads * sizeof(pthread_t));
    ThreadArg *thread_args = (ThreadArg *)malloc(num_threads * sizeof(ThreadArg));
    
    if (!threads || !thread_args) {
        fprintf(stderr, "Error: Thread allocation failed\n");
        free(array);
        free(threads);
        free(thread_args);
        pthread_mutex_destroy(&sum_mutex);
        return 1;
    }
    
    // 计算每个线程负责的元素范围
    long long chunk_size = array_size / num_threads;
    long long remainder = array_size % num_threads;
    long long current_start = 0;
    
    for (int i = 0; i < num_threads; i++) {
        thread_args[i].thread_id = i;
        thread_args[i].start_idx = current_start;
        
        // 前 remainder 个线程多处理一个元素
        long long my_chunk = chunk_size + (i < remainder ? 1 : 0);
        thread_args[i].end_idx = current_start + my_chunk;
        thread_args[i].local_sum = 0;
        
        current_start = thread_args[i].end_idx;
    }
    
    // 开始计时
    double start_time = get_time();
    
    // 创建并启动线程
    for (int i = 0; i < num_threads; i++) {
        int rc = pthread_create(&threads[i], NULL, sum_thread, &thread_args[i]);
        if (rc) {
            fprintf(stderr, "Error: Failed to create thread %d, return code %d\n", i, rc);
            free(array);
            free(threads);
            free(thread_args);
            pthread_mutex_destroy(&sum_mutex);
            return 1;
        }
    }
    
    // 等待所有线程完成
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // 结束计时
    double end_time = get_time();
    double elapsed = end_time - start_time;
    
    // 输出结果（仅输出指定格式）
    printf("Strategy: %s, Size: %lld, Threads: %d, Sum: %lld, Time: %.6f s\n", 
           strategy_names[strategy], array_size, num_threads, global_sum, elapsed);
    
    // 释放资源
    free(array);
    free(threads);
    free(thread_args);
    pthread_mutex_destroy(&sum_mutex);
    
    return 0;
}