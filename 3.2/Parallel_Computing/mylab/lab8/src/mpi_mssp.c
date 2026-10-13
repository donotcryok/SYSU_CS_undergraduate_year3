/**
 * mpi_mssp.c – MPI parallel Floyd-Warshall APSP
 * Usage: mpirun -np <P> ./mpi_mssp <csv_file> <output_prefix>
 *
 * Each process owns a contiguous block of rows.
 * At each k-iteration the owner of row k broadcasts it via MPI_Bcast.
 */
#include "graph.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 3) {
        if (rank == 0)
            fprintf(stderr, "Usage: mpirun -np <P> %s <csv> <out_prefix>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    Graph *g = NULL;
    int V = 0;

    /* ---- rank 0 reads the graph and broadcasts meta-data ---- */
    if (rank == 0) {
        g = read_graph(argv[1]);
        V = g->V;
    }
    MPI_Bcast(&V, 1, MPI_INT, 0, MPI_COMM_WORLD);

    /* ---- row partitioning ---- */
    int rows_per = (V + size - 1) / size;
    int my_start = rank * rows_per;
    int my_end   = my_start + rows_per;
    if (my_end > V) my_end = V;
    int my_rows = my_end - my_start;

    /* allocate local distance sub-matrix: my_rows × V */
    double *local_dist = malloc((size_t)my_rows * V * sizeof(double));
    if (!local_dist) { perror("malloc"); MPI_Abort(MPI_COMM_WORLD, 1); }

    /* rank 0 distributes rows via MPI_Scatterv */
    if (rank == 0) {
        int *sendcounts = malloc(size * sizeof(int));
        int *displs     = malloc(size * sizeof(int));
        for (int p = 0; p < size; p++) {
            int p_start = p * rows_per;
            int p_end   = p_start + rows_per;
            if (p_end > V) p_end = V;
            sendcounts[p] = (p_end - p_start) * V;
            displs[p]     = p_start * V;
        }
        MPI_Scatterv(g->dist, sendcounts, displs, MPI_DOUBLE,
                     local_dist, my_rows * V, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        free(sendcounts);
        free(displs);
    } else {
        MPI_Scatterv(NULL, NULL, NULL, MPI_DOUBLE,
                     local_dist, my_rows * V, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    }

    /* buffer for receiving a full row k */
    double *row_k = malloc(V * sizeof(double));

    double t0 = MPI_Wtime();

    /* ---- Floyd-Warshall ---- */
    for (int k = 0; k < V; k++) {
        /* determine who owns row k */
        int owner = k / rows_per;

        if (rank == owner) {
            int local_idx = k - my_start;
            memcpy(row_k, &local_dist[local_idx * V], V * sizeof(double));
        }
        MPI_Bcast(row_k, V, MPI_DOUBLE, owner, MPI_COMM_WORLD);

        /* update local rows */
        for (int li = 0; li < my_rows; li++) {
            int global_i = my_start + li;
            if (global_i == k) continue;
            double dik = local_dist[li * V + k];
            if (dik >= INF_VAL * 0.5) continue;
            double *di = &local_dist[li * V];
            for (int j = 0; j < V; j++) {
                double nd = dik + row_k[j];
                if (nd < di[j]) di[j] = nd;
            }
        }
    }

    double t1 = MPI_Wtime();

    /* ---- gather results back to rank 0 ---- */
    if (rank == 0) {
        int *recvcounts = malloc(size * sizeof(int));
        int *rdispls    = malloc(size * sizeof(int));
        for (int p = 0; p < size; p++) {
            int p_start = p * rows_per;
            int p_end   = p_start + rows_per;
            if (p_end > V) p_end = V;
            recvcounts[p] = (p_end - p_start) * V;
            rdispls[p]    = p_start * V;
        }
        MPI_Gatherv(local_dist, my_rows * V, MPI_DOUBLE,
                    g->dist, recvcounts, rdispls, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        free(recvcounts);
        free(rdispls);
    } else {
        MPI_Gatherv(local_dist, my_rows * V, MPI_DOUBLE,
                    NULL, NULL, NULL, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    }

    double elapsed = t1 - t0;
    if (rank == 0) {
        printf("TIME: %.6f\n", elapsed);
        char fname[512];
        snprintf(fname, sizeof(fname), "result/%s_distance.txt", argv[2]);
        write_distances(fname, g);
        free_graph(g);
    }

    free(local_dist);
    free(row_k);
    MPI_Finalize();
    return 0;
}
