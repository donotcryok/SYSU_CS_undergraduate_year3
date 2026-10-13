NVCC := nvcc
NVCC_FLAGS := -O3 -arch=sm_89

.PHONY: all clean hello transpose

all: hello transpose

hello: hello.cu
	$(NVCC) $(NVCC_FLAGS) -o hello hello.cu

transpose: transpose.cu
	$(NVCC) $(NVCC_FLAGS) -o transpose transpose.cu

clean:
	rm -f hello transpose
	rm -f *.o
