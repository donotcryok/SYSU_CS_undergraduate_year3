#include "graph.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_TEST_PAIRS 20
#define MAX_LINE_LEN   256

/* ------------------------------------------------------------------ */
/*  read_graph – Parse a CSV (source,target,distance), build           */
/*               symmetric adjacency matrix, remap vertex ids.         */
/* ------------------------------------------------------------------ */
Graph *read_graph(const char *filename)
{
    FILE *fp = fopen(filename, "r");
    if (!fp) { perror(filename); exit(EXIT_FAILURE); }

    /* ---------- first pass: discover vertex set ---------- */
    char line[MAX_LINE_LEN];
    if (!fgets(line, sizeof(line), fp)) {  /* skip header */
        fclose(fp); return NULL;
    }

    int max_id = -1;
    int cap_edges = 65536;
    int *src_buf = malloc(cap_edges * sizeof(int));
    int *tgt_buf = malloc(cap_edges * sizeof(int));
    double *wgt_buf = malloc(cap_edges * sizeof(double));
    int num_edges = 0;

    while (fgets(line, sizeof(line), fp)) {
        int s, t; double w;
        if (sscanf(line, "%d,%d,%lf", &s, &t, &w) != 3) continue;
        if (s > max_id) max_id = s;
        if (t > max_id) max_id = t;

        if (num_edges >= cap_edges) {
            cap_edges *= 2;
            src_buf = realloc(src_buf, cap_edges * sizeof(int));
            tgt_buf = realloc(tgt_buf, cap_edges * sizeof(int));
            wgt_buf = realloc(wgt_buf, cap_edges * sizeof(double));
        }
        src_buf[num_edges] = s;
        tgt_buf[num_edges] = t;
        wgt_buf[num_edges] = w;
        num_edges++;
    }
    fclose(fp);

    int max_orig = max_id + 1;   /* range [0, max_orig) */
    int V = max_orig;

    /* ---------- second pass: build remap ---------- */
    Graph *g = malloc(sizeof(Graph));
    g->V          = V;
    g->V_orig_max = max_orig;
    g->test_count = (num_edges < MAX_TEST_PAIRS) ? num_edges : MAX_TEST_PAIRS;

    g->orig2local = malloc(max_orig * sizeof(int));
    g->local2orig = malloc(V * sizeof(int));
    for (int i = 0; i < max_orig; i++) g->orig2local[i] = i;
    for (int i = 0; i < V; i++)       g->local2orig[i] = i;

    /* ---------- allocate & init distance matrix ---------- */
    size_t mat_sz = (size_t)V * V;
    g->dist = malloc(mat_sz * sizeof(double));
    for (size_t i = 0; i < mat_sz; i++) g->dist[i] = INF_VAL;
    for (int i = 0; i < V; i++) g->dist[i * V + i] = 0.0;

    /* fill edges (undirected – symmetric) */
    for (int e = 0; e < num_edges; e++) {
        int u = src_buf[e], v = tgt_buf[e];
        double w = wgt_buf[e];
        if (w < g->dist[u * V + v]) {
            g->dist[u * V + v] = w;
            g->dist[v * V + u] = w;
        }
    }
    free(src_buf); free(tgt_buf); free(wgt_buf);

    /* store test pairs (first MAX_TEST_PAIRS edges) */
    fp = fopen(filename, "r");
    if (!fp) { perror(filename); exit(EXIT_FAILURE); }
    (void)fgets(line, sizeof(line), fp);  /* skip header */
    g->test_src = malloc(g->test_count * sizeof(int));
    g->test_tgt = malloc(g->test_count * sizeof(int));
    int tpi = 0;
    while (tpi < g->test_count && fgets(line, sizeof(line), fp)) {
        int s, t; double w;
        if (sscanf(line, "%d,%d,%lf", &s, &t, &w) == 3) {
            g->test_src[tpi] = s;
            g->test_tgt[tpi] = t;
            tpi++;
        }
    }
    fclose(fp);
    g->test_count = tpi;

    return g;
}

void free_graph(Graph *g)
{
    if (!g) return;
    free(g->dist);
    free(g->orig2local);
    free(g->local2orig);
    free(g->test_src);
    free(g->test_tgt);
    free(g);
}

void write_distances(const char *filepath, const Graph *g)
{
    FILE *fp = fopen(filepath, "w");
    if (!fp) { perror(filepath); return; }
    for (int k = 0; k < g->test_count; k++) {
        int s = g->test_src[k];
        int t = g->test_tgt[k];
        double d = g->dist[s * g->V + t];
        fprintf(fp, "%.10f\n", d);
    }
    fclose(fp);
}

double get_inf(void) { return INF_VAL; }
