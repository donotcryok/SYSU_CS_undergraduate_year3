/**
 * heated_plate_pthread.c — 使用原生 Pthreads 的热传导模拟
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <pthread.h>

static int    g_M, g_N, g_num_thr;
static double g_epsilon;

static double *g_u = NULL;
static double *g_w = NULL;
static volatile double g_diff;
static double  g_mean;
static volatile int g_done = 0;

static pthread_barrier_t g_barrier;

static double get_time_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

typedef struct {
    int    row_start, row_end;
    double my_diff;
    double local_mean;
} worker_ctx_t;

static void *worker_main(void *arg)
{
    worker_ctx_t *ctx = (worker_ctx_t *)arg;
    const int rs = ctx->row_start, re = ctx->row_end;
    const int N  = g_N, M = g_M;

#define U(i,j) g_u[(i)*N + (j)]
#define W(i,j) g_w[(i)*N + (j)]

    /* ── 初始化：边界 + 内部 ── */
    for (int i = rs; i < re; i++) {
        if (i >= 1 && i < M - 1) { W(i,0) = 100.0; W(i,N-1) = 100.0; }
    }
    if (rs <= 0   && 0 < re)   for (int j = 0; j < N; j++) W(0,j)   = 0.0;
    if (rs <= M-1 && M-1 < re) for (int j = 0; j < N; j++) W(M-1,j) = 100.0;

    double lmean = 0.0;
    for (int i = rs; i < re; i++) {
        if (i >= 1 && i < M-1) lmean += W(i,0) + W(i,N-1);
    }
    if (rs == 0)   for (int j = 0; j < N; j++) lmean += W(0,j);
    if (rs <= M-1 && M-1 < re) for (int j = 0; j < N; j++) lmean += W(M-1,j);
    ctx->local_mean = lmean;

    pthread_barrier_wait(&g_barrier);  /* 主线程汇总 mean */

    for (int i = rs; i < re; i++) {
        if (i >= 1 && i < M-1)
            for (int j = 1; j < N-1; j++) W(i,j) = g_mean;
    }
    pthread_barrier_wait(&g_barrier);  /* 初始化完成 */

    /* ── 迭代主循环 ── */
    while (!g_done) {
        /* save + compute new */
        for (int i = rs; i < re; i++) {
            for (int j = 0; j < N; j++) U(i,j) = W(i,j);
        }
        for (int i = rs; i < re; i++) {
            if (i >= 1 && i < M-1) {
                for (int j = 1; j < N-1; j++) {
                    W(i,j) = (U(i-1,j) + U(i+1,j) + U(i,j-1) + U(i,j+1)) * 0.25;
                }
            }
        }
        pthread_barrier_wait(&g_barrier);  /* A: save+new done */

        /* compute local diff */
        double md = 0.0;
        for (int i = rs; i < re; i++) {
            if (i >= 1 && i < M-1) {
                for (int j = 1; j < N-1; j++) {
                    double d = fabs(W(i,j) - U(i,j));
                    if (d > md) md = d;
                }
            }
        }
        ctx->my_diff = md;
        pthread_barrier_wait(&g_barrier);  /* B: local diff done */

        /*
         * barrier C: 确保主线程已汇总 g_diff 并更新 g_done，
         * 然后再由 while(!g_done) 检查 — 消除竞态。
         */
        pthread_barrier_wait(&g_barrier);  /* C: sync g_done state */
    }

#undef U
#undef W
    return NULL;
}

int main(int argc, char *argv[])
{
    int M = (argc > 1) ? atoi(argv[1]) : 500;
    int N = (argc > 2) ? atoi(argv[2]) : 500;
    double epsilon = (argc > 3) ? atof(argv[3]) : 0.001;
    int num_thr   = (argc > 4) ? atoi(argv[4]) : 1;

    if (M <= 0) M = 500;
    if (N <= 0) N = 500;
    if (epsilon <= 0.0) epsilon = 0.001;
    if (num_thr <= 0) num_thr = 1;

    g_M = M; g_N = N; g_num_thr = num_thr; g_epsilon = epsilon;

    /* ── 单线程快速路径 ── */
    if (num_thr == 1) {
        size_t ms = (size_t)M * N * sizeof(double);
        double *w = (double *)aligned_alloc(64, ms);
        double *u = (double *)aligned_alloc(64, ms);
        double mean = 0.0;
        double diff;
        int it = 0, itp = 1;

        for (int i = 1; i < M-1; i++) { w[i*N+0]=100.0; w[i*N+N-1]=100.0; }
        for (int j = 0; j < N; j++)   { w[0*N+j]=0.0;   w[(M-1)*N+j]=100.0; }
        for (int i = 1; i < M-1; i++) mean += w[i*N+0] + w[i*N+N-1];
        for (int j = 0; j < N; j++)   mean += w[0*N+j] + w[(M-1)*N+j];
        mean /= (double)(2*M + 2*N - 4);

        printf("\nHEATED_PLATE_PTHREAD (native pthreads, serial)\n");
        printf("  Grid: %d x %d\n  Epsilon: %e\n  Threads: 1\n", M, N, epsilon);
        printf("  MEAN = %f\n\n Iteration  Change\n\n", mean);

        for (int i = 1; i < M-1; i++)
            for (int j = 1; j < N-1; j++) w[i*N+j] = mean;

        double t0 = get_time_sec();
        diff = epsilon;
        while (epsilon <= diff) {
            for (int i = 0; i < M; i++)
                for (int j = 0; j < N; j++) u[i*N+j] = w[i*N+j];
            for (int i = 1; i < M-1; i++)
                for (int j = 1; j < N-1; j++)
                    w[i*N+j] = (u[(i-1)*N+j] + u[(i+1)*N+j] + u[i*N+j-1] + u[i*N+j+1]) * 0.25;
            diff = 0.0;
            for (int i = 1; i < M-1; i++)
                for (int j = 1; j < N-1; j++) {
                    double d = fabs(w[i*N+j] - u[i*N+j]);
                    if (d > diff) diff = d;
                }
            it++; if (it == itp) { printf("  %8d  %f\n", it, diff); itp *= 2; }
        }
        double wt = get_time_sec() - t0;
        printf("\n  %8d  %f\n\n  Error tolerance achieved.\n", it, diff);
        printf("  Wallclock time = %f\n\nHEATED_PLATE_PTHREAD: Normal end of execution.\n", wt);
        fprintf(stderr, "CSV,%d,%d,%e,1,%f\n", M, N, epsilon, wt);
        free(w); free(u);
        return 0;
    }

    printf("\nHEATED_PLATE_PTHREAD (native pthreads)\n");
    printf("  Grid: %d x %d\n  Epsilon: %e\n  Threads: %d\n", M, N, epsilon, num_thr);
    fflush(stdout);

    size_t ms = (size_t)M * N * sizeof(double);
    g_u = (double *)aligned_alloc(64, ms);
    g_w = (double *)aligned_alloc(64, ms);
    if (!g_u || !g_w) { fprintf(stderr, "malloc failed\n"); return 1; }

    pthread_barrier_init(&g_barrier, NULL, (unsigned)(num_thr + 1));

    pthread_t    *threads = malloc((size_t)num_thr * sizeof(pthread_t));
    worker_ctx_t *ctxs    = malloc((size_t)num_thr * sizeof(worker_ctx_t));

    int base = M / num_thr, rem = M % num_thr, rpos = 0;
    for (int t = 0; t < num_thr; t++) {
        int chunk = base + (t < rem ? 1 : 0);
        ctxs[t].row_start = rpos; ctxs[t].row_end = rpos + chunk;
        ctxs[t].my_diff = 0.0; ctxs[t].local_mean = 0.0;
        rpos += chunk;
    }

    for (int t = 0; t < num_thr; t++)
        pthread_create(&threads[t], NULL, worker_main, &ctxs[t]);

    pthread_barrier_wait(&g_barrier);  /* mean 汇总 */
    g_mean = 0.0;
    for (int t = 0; t < num_thr; t++) g_mean += ctxs[t].local_mean;
    g_mean /= (double)(2 * M + 2 * N - 4);
    printf("  MEAN = %f\n\n Iteration  Change\n\n", g_mean);
    fflush(stdout);

    pthread_barrier_wait(&g_barrier);  /* 内部初始化完成 */

    int iterations = 0, iterations_print = 1;
    double wtime_start = get_time_sec();
    g_diff = epsilon;
    g_done = 0;

    while (g_diff >= epsilon) {
        pthread_barrier_wait(&g_barrier);  /* A: save+new done */
        pthread_barrier_wait(&g_barrier);  /* B: local diff done */

        g_diff = 0.0;
        for (int t = 0; t < num_thr; t++)
            if (ctxs[t].my_diff > g_diff) g_diff = ctxs[t].my_diff;

        iterations++;
        if (iterations == iterations_print) {
            printf("  %8d  %f\n", iterations, g_diff);
            fflush(stdout); iterations_print *= 2;
        }

        /* 收敛后设置标志，通过 barrier C 广播给工作线程 */
        if (g_diff <= epsilon) g_done = 1;
        pthread_barrier_wait(&g_barrier);  /* C: sync g_done state */
    }
    double wtime = get_time_sec() - wtime_start;

    printf("\n  %8d  %f\n\n  Error tolerance achieved.\n", iterations, g_diff);
    printf("  Wallclock time = %f\n\nHEATED_PLATE_PTHREAD: Normal end of execution.\n", wtime);
    fprintf(stderr, "CSV,%d,%d,%e,%d,%f\n", M, N, epsilon, num_thr, wtime);

    for (int t = 0; t < num_thr; t++) pthread_join(threads[t], NULL);
    pthread_barrier_destroy(&g_barrier);
    free(threads); free(ctxs); free(g_u); free(g_w);
    return 0;
}
