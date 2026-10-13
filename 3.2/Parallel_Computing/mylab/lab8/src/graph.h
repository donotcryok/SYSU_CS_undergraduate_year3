#ifndef GRAPH_H
#define GRAPH_H

#include <stddef.h>

#define INF_VAL 1e18

typedef struct {
    int   V;           /* number of vertices (ids are 0..V-1 after remap) */
    int   V_orig_max;  /* maximum original vertex id + 1              */
    double *dist;      /* flattened V×V distance matrix, row-major    */
    int   *orig2local; /* mapping from original id → local id         */
    int   *local2orig; /* mapping from local id → original id         */

    /* test pairs extracted from the first N edges of the CSV */
    int   *test_src;
    int   *test_tgt;
    int    test_count;
} Graph;

Graph *read_graph(const char *filename);
void   free_graph(Graph *g);
void   write_distances(const char *filepath, const Graph *g);
double get_inf(void);

#endif
