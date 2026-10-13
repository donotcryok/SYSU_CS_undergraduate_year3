/**
 * pth_mssp.c – Pthreads parallel Floyd-Warshall APSP
 * Usage: ./pth_mssp <csv_file> <num_threads> <output_prefix>
 *
 * Clean barrier-based design. For nthreads==1, uses a direct serial path.
 * For nthreads>=2, uses nthreads barriers (master + nthreads-1 workers).
 */
#include "graph.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

typedef struct {
    int    tid;
    int    nthreads;
    int    V;
    double *dist;
    int    start_row, end_row;
    volatile int *k_shared;       /* current pivot row, -1 = terminate */
    pthread_barrier_t *bar;
} ThreadArg;

static void *worker(void *arg_)
{
    ThreadArg *a = (ThreadArg *)arg_;
    int V = a->V;
    double *dist = a->dist;
    pthread_barrier_t *bar = a->bar;

    pthread_barrier_wait(bar);   /* ready signal */

    for (;;) {
        pthread_barrier_wait(bar);   /* wait for k to be published */

        int k = *a->k_shared;
        if (k < 0) break;

        double *dk = &dist[k * V];
        for (int i = a->start_row; i < a->end_row; i++) {
            double dik = dist[i * V + k];
            if (dik >= INF_VAL * 0.5) continue;
            double *di = &dist[i * V];
            for (int j = 0; j < V; j++) {
                double nd = dik + dk[j];
                if (nd < di[j]) di[j] = nd;
            }
        }

        pthread_barrier_wait(bar);   /* signal completion */
    }
    return NULL;
}

static double wall_time(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void serial_fw(int V, double *dist)
{
    for (int k = 0; k < V; k++) {
        double *dk = &dist[k * V];
        for (int i = 0; i < V; i++) {
            double dik = dist[i * V + k];
            if (dik >= INF_VAL * 0.5) continue;
            double *di = &dist[i * V];
            for (int j = 0; j < V; j++) {
                double nd = dik + dk[j];
                if (nd < di[j]) di[j] = nd;
            }
        }
    }
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <csv> <nthreads> <out_prefix>\n", argv[0]);
        return 1;
    }
    int nthreads = atoi(argv[2]);
    if (nthreads < 1) nthreads = 1;

    Graph *g = read_graph(argv[1]);
    int V = g->V;
    double *dist = g->dist;

    /* ---- serial fast-path ---- */
    if (nthreads == 1) {
        double t0 = wall_time();
        serial_fw(V, dist);
        double t1 = wall_time();
        printf("TIME: %.6f\n", t1 - t0);
        char fname[512];
        snprintf(fname, sizeof(fname), "result/%s_distance.txt", argv[3]);
        write_distances(fname, g);
        free_graph(g);
        return 0;
    }

    /* ---- parallel (nthreads >= 2) ---- */
    int rows_per = (V + nthreads - 1) / nthreads;
    int k_shared = 0;

    pthread_barrier_t bar;
    pthread_barrier_init(&bar, NULL, nthreads);

    pthread_t *tids = malloc((nthreads - 1) * sizeof(pthread_t));
    ThreadArg *args = malloc(nthreads * sizeof(ThreadArg));

    for (int t = 0; t < nthreads; t++) {
        args[t].tid       = t;
        args[t].nthreads  = nthreads;
        args[t].V         = V;
        args[t].dist      = dist;
        args[t].start_row = t * rows_per;
        args[t].end_row   = args[t].start_row + rows_per;
        if (args[t].end_row > V) args[t].end_row = V;
        args[t].k_shared  = &k_shared;
        args[t].bar       = &bar;
    }
    /* create workers (tid 0..nthreads-2), master is tid=nthreads-1 */
    for (int t = 0; t < nthreads - 1; t++)
        pthread_create(&tids[t], NULL, worker, &args[t]);

    int master_tid = nthreads - 1;

    /* synchronize startup */
    pthread_barrier_wait(&bar);

    double t0 = wall_time();

    for (int k = 0; k < V; k++) {
        k_shared = k;
        pthread_barrier_wait(&bar);    /* publish k, workers compute */

        /* master computes its own chunk */
        {
            int st = args[master_tid].start_row;
            int en = args[master_tid].end_row;
            double *dk = &dist[k * V];
            for (int i = st; i < en; i++) {
                double dik = dist[i * V + k];
                if (dik >= INF_VAL * 0.5) continue;
                double *di = &dist[i * V];
                for (int j = 0; j < V; j++) {
                    double nd = dik + dk[j];
                    if (nd < di[j]) di[j] = nd;
                }
            }
        }

        pthread_barrier_wait(&bar);    /* wait for workers to finish */
    }

    double t1 = wall_time();

    /* terminate workers */
    k_shared = -1;
    pthread_barrier_wait(&bar);
    for (int t = 0; t < nthreads - 1; t++)
        pthread_join(tids[t], NULL);

    pthread_barrier_destroy(&bar);
    free(tids);
    free(args);

    printf("TIME: %.6f\n", t1 - t0);
    {
        char fname[512];
        snprintf(fname, sizeof(fname), "result/%s_distance.txt", argv[3]);
        write_distances(fname, g);
    }
    free_graph(g);
    return 0;
}
