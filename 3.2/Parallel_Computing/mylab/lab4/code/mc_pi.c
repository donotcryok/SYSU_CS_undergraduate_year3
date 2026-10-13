/**
 * mc_pi.c - 使用Pthreads并行蒙特卡洛方法计算Pi
 */

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <math.h>

// 全局变量
long long total_points;        // 总点数
long long points_in_circle;    // 落在圆内的点数
int num_threads;               // 线程数
pthread_mutex_t mutex;         // 用于汇总结果的互斥锁

// 线程参数结构
typedef struct {
    int thread_id;             // 线程ID
    long long local_count;     // 局部计数器
    long long local_total;     // 局部总点数
    unsigned int seed;         // 随机数种子（每个线程独立）
} ThreadData;

// 线程函数
void* monte_carlo_thread(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    long long points_per_thread = total_points / num_threads;
    data->local_total = points_per_thread;
    data->local_count = 0;
    
    // 使用rand_r和独立种子生成随机数
    for (long long i = 0; i < points_per_thread; i++) {
        // 生成 [0, 1] 范围内的随机坐标
        double x = (double)rand_r(&data->seed) / RAND_MAX;
        double y = (double)rand_r(&data->seed) / RAND_MAX;
        
        // 检查是否落在单位圆内
        if (x * x + y * y <= 1.0) {
            data->local_count++;
        }
    }
    
    // 使用互斥锁汇总结果
    pthread_mutex_lock(&mutex);
    points_in_circle += data->local_count;
    pthread_mutex_unlock(&mutex);
    
    return NULL;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        fprintf(stderr, "用法: %s <N> <num_threads>\n", argv[0]);
        fprintf(stderr, "  N: 总采样点数\n");
        fprintf(stderr, "  num_threads: 线程数\n");
        return 1;
    }
    
    total_points = atoll(argv[1]);
    num_threads = atoi(argv[2]);
    
    if (total_points <= 0) {
        fprintf(stderr, "错误: N必须为正整数\n");
        return 1;
    }
    
    if (num_threads <= 0) {
        fprintf(stderr, "错误: 线程数必须为正整数\n");
        return 1;
    }
    
    // 初始化全局变量
    points_in_circle = 0;
    pthread_mutex_init(&mutex, NULL);
    
    // 分配线程和数据
    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    ThreadData* thread_data = (ThreadData*)malloc(num_threads * sizeof(ThreadData));
    
    // 开始计时
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // 创建线程，每个线程有独立的随机种子
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].thread_id = i;
        // 使用不同的种子确保每个线程生成不同的随机序列
        thread_data[i].seed = (unsigned int)(time(NULL) + i * 12345);
        pthread_create(&threads[i], NULL, monte_carlo_thread, &thread_data[i]);
    }
    
    // 等待所有线程完成
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // 结束计时
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    // 计算Pi
    double pi_estimate = 4.0 * points_in_circle / total_points;
    
    // 计算耗时（毫秒）
    double elapsed = (end.tv_sec - start.tv_sec) * 1000.0;
    elapsed += (end.tv_nsec - start.tv_nsec) / 1e6;
    
    // 输出结果
    printf("========================================\n");
    printf("蒙特卡洛方法计算Pi\n");
    printf("========================================\n");
    printf("总采样点数: %lld\n", total_points);
    printf("线程数: %d\n", num_threads);
    printf("落在圆内的点数: %lld\n", points_in_circle);
    printf("----------------------------------------\n");
    printf("估计的Pi值: %.10f\n", pi_estimate);
    printf("真实Pi值:   %.10f\n", M_PI);
    printf("误差: %.10f (%.6f%%)\n", 
           fabs(pi_estimate - M_PI), 
           fabs(pi_estimate - M_PI) / M_PI * 100);
    printf("----------------------------------------\n");
    printf("计算耗时: %.3f 毫秒\n", elapsed);
    printf("========================================\n");
    
    // 清理资源
    pthread_mutex_destroy(&mutex);
    free(threads);
    free(thread_data);
    
    return 0;
}