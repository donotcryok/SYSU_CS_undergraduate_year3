/**
 * eq_solver.c - 使用Pthreads和条件变量求解一元二次方程
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <time.h>

// 共享数据结构
typedef struct {
    double a, b, c;         // 方程系数
    double delta;           // Δ = b² - 4ac
    double sqrt_delta;      // √Δ
    double x1, x2;          // 方程的根
    int has_real_roots;     // 是否有实根
    
    // 同步原语
    pthread_mutex_t mutex;
    pthread_cond_t cond_delta;       // Δ计算完成
    pthread_cond_t cond_sqrt_delta;  // √Δ计算完成
    pthread_cond_t cond_roots;       // 根计算完成
    
    int delta_ready;        // Δ已计算
    int sqrt_delta_ready;   // √Δ已计算
    int x1_ready;           // x1已计算
    int x2_ready;           // x2已计算
} SharedData;

// Thread 1: 计算Δ
void* compute_delta(void* arg) {
    SharedData* data = (SharedData*)arg;
    
    pthread_mutex_lock(&data->mutex);
    
    // 计算Δ = b² - 4ac
    data->delta = data->b * data->b - 4 * data->a * data->c;
    
    // 判断是否有实根
    if (data->delta >= 0) {
        data->has_real_roots = 1;
    } else {
        data->has_real_roots = 0;
    }
    
    data->delta_ready = 1;
    
    // 唤醒等待Δ的线程
    pthread_cond_signal(&data->cond_delta);
    
    pthread_mutex_unlock(&data->mutex);
    
    return NULL;
}

// Thread 2: 计算√Δ
void* compute_sqrt_delta(void* arg) {
    SharedData* data = (SharedData*)arg;
    
    pthread_mutex_lock(&data->mutex);
    
    // 等待Δ计算完成
    while (!data->delta_ready) {
        pthread_cond_wait(&data->cond_delta, &data->mutex);
    }
    
    // 只有当Δ >= 0时才计算√Δ
    if (data->has_real_roots) {
        data->sqrt_delta = sqrt(data->delta);
    } else {
        data->sqrt_delta = 0;
    }
    
    data->sqrt_delta_ready = 1;
    
    // 唤醒等待√Δ的线程（x1和x2的计算线程）
    pthread_cond_broadcast(&data->cond_sqrt_delta);
    
    pthread_mutex_unlock(&data->mutex);
    
    return NULL;
}

// Thread 3: 计算x1
void* compute_x1(void* arg) {
    SharedData* data = (SharedData*)arg;
    
    pthread_mutex_lock(&data->mutex);
    
    // 等待√Δ计算完成
    while (!data->sqrt_delta_ready) {
        pthread_cond_wait(&data->cond_sqrt_delta, &data->mutex);
    }
    
    // 计算x1 = (-b + √Δ) / (2a)
    if (data->has_real_roots) {
        data->x1 = (-data->b + data->sqrt_delta) / (2 * data->a);
    } else {
        data->x1 = NAN;
    }
    
    data->x1_ready = 1;
    pthread_cond_signal(&data->cond_roots);
    
    pthread_mutex_unlock(&data->mutex);
    
    return NULL;
}

// Thread 4: 计算x2
void* compute_x2(void* arg) {
    SharedData* data = (SharedData*)arg;
    
    pthread_mutex_lock(&data->mutex);
    
    // 等待√Δ计算完成
    while (!data->sqrt_delta_ready) {
        pthread_cond_wait(&data->cond_sqrt_delta, &data->mutex);
    }
    
    // 计算x2 = (-b - √Δ) / (2a)
    if (data->has_real_roots) {
        data->x2 = (-data->b - data->sqrt_delta) / (2 * data->a);
    } else {
        data->x2 = NAN;
    }
    
    data->x2_ready = 1;
    pthread_cond_signal(&data->cond_roots);
    
    pthread_mutex_unlock(&data->mutex);
    
    return NULL;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        fprintf(stderr, "用法: %s <a> <b> <c>\n", argv[0]);
        fprintf(stderr, "求解方程 ax² + bx + c = 0\n");
        return 1;
    }
    
    // 初始化共享数据
    SharedData data;
    data.a = atof(argv[1]);
    data.b = atof(argv[2]);
    data.c = atof(argv[3]);
    data.delta_ready = 0;
    data.sqrt_delta_ready = 0;
    data.x1_ready = 0;
    data.x2_ready = 0;
    
    // 检查a是否为0
    if (data.a == 0) {
        fprintf(stderr, "错误: a不能为0（不是二次方程）\n");
        return 1;
    }
    
    // 初始化互斥锁和条件变量
    pthread_mutex_init(&data.mutex, NULL);
    pthread_cond_init(&data.cond_delta, NULL);
    pthread_cond_init(&data.cond_sqrt_delta, NULL);
    pthread_cond_init(&data.cond_roots, NULL);
    
    // 创建线程
    pthread_t t1, t2, t3, t4;
    
    // 开始计时
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    pthread_create(&t1, NULL, compute_delta, &data);
    pthread_create(&t2, NULL, compute_sqrt_delta, &data);
    pthread_create(&t3, NULL, compute_x1, &data);
    pthread_create(&t4, NULL, compute_x2, &data);
    
    // 等待所有线程完成
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    pthread_join(t4, NULL);
    
    // 结束计时
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    // 计算耗时（微秒）
    double elapsed = (end.tv_sec - start.tv_sec) * 1e6;
    elapsed += (end.tv_nsec - start.tv_nsec) / 1e3;
    
    // 输出结果
    printf("========================================\n");
    printf("方程: %.2fx² + %.2fx + %.2f = 0\n", data.a, data.b, data.c);
    printf("========================================\n");
    printf("Δ = b² - 4ac = %.6f\n", data.delta);
    printf("√Δ = %.6f\n", data.sqrt_delta);
    printf("----------------------------------------\n");
    
    if (data.has_real_roots) {
        if (data.delta == 0) {
            printf("方程有一个实根（重根）:\n");
            printf("  x = %.6f\n", data.x1);
        } else {
            printf("方程有两个实根:\n");
            printf("  x₁ = %.6f\n", data.x1);
            printf("  x₂ = %.6f\n", data.x2);
        }
    } else {
        printf("方程无实根，有两个共轭复根:\n");
        double real_part = -data.b / (2 * data.a);
        double imag_part = sqrt(-data.delta) / (2 * data.a);
        printf("  x₁ = %.6f + %.6fi\n", real_part, imag_part);
        printf("  x₂ = %.6f - %.6fi\n", real_part, imag_part);
    }
    
    printf("----------------------------------------\n");
    printf("多线程计算耗时: %.2f 微秒\n", elapsed);
    printf("========================================\n");
    
    // 清理资源
    pthread_mutex_destroy(&data.mutex);
    pthread_cond_destroy(&data.cond_delta);
    pthread_cond_destroy(&data.cond_sqrt_delta);
    pthread_cond_destroy(&data.cond_roots);
    
    return 0;
}