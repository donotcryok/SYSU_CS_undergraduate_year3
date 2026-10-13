# Makefile – Multi-target build for MSSP parallel implementations
CC      = gcc
MPICC   = mpicc
CFLAGS  = -O3 -Wall -march=native
LDFLAGS =

# OpenMP version
OMP_SRC  = omp_mssp.c graph.c
OMP_BIN  = omp_mssp
OMP_FLAGS = -fopenmp

# Pthreads version
PTH_SRC  = pth_mssp.c graph.c
PTH_BIN  = pth_mssp
PTH_FLAGS = -lpthread

# MPI version
MPI_SRC  = mpi_mssp.c graph.c
MPI_BIN  = mpi_mssp

.PHONY: all clean omp pth mpi

all: omp pth mpi

omp: $(OMP_SRC) graph.h
	$(CC) $(CFLAGS) $(OMP_FLAGS) -o $(OMP_BIN) $(OMP_SRC) $(LDFLAGS)

pth: $(PTH_SRC) graph.h
	$(CC) $(CFLAGS) $(PTH_FLAGS) -o $(PTH_BIN) $(PTH_SRC) $(LDFLAGS)

mpi: $(MPI_SRC) graph.h
	$(MPICC) $(CFLAGS) -o $(MPI_BIN) $(MPI_SRC) $(LDFLAGS)

clean:
	rm -f $(OMP_BIN) $(PTH_BIN) $(MPI_BIN)
