CXX = mpicxx
CXXFLAGS = -O2 -Wall
LDFLAGS = -lm

.PHONY: all serial mpi mpi_opt clean

all: fft_serial fft_mpi fft_mpi_opt

serial: fft_serial

fft_serial: fft_serial.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

mpi: fft_mpi

fft_mpi: fft_mpi.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

mpi_opt: fft_mpi_opt

fft_mpi_opt: fft_mpi_opt.cpp
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f fft_serial fft_mpi fft_mpi_opt
	rm -f massif.out.*
	rm -f results.csv
