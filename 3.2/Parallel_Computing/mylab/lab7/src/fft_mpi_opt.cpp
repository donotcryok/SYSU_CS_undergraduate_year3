/**
 * fft_mpi_opt.cpp — MPI 并行 FFT (MPI_Pack/Unpack 优化版)
 *
 * 算法：Transpose FFT (与 fft_mpi.cpp 相同)
 *   将 N 点数据映射为 P×Q 矩阵（行主序），N = P×Q, Q = N/P。
 *
 *   正变换 (Forward, sgn=+1):
 *     T · FFT_P(+1) · twiddle · T · FFT_Q(+1)
 *   逆变换 (Inverse, sgn=-1):
 *     FFT_Q(-1) · T · conj(twiddle) · FFT_P(-1) · T / N
 *
 * 优化：使用 MPI_Pack/Unpack 将非连续数据序列化，
 *   减少 MPI_Alltoall 中自动打包/解包的开销。
 *
 * Petersen 约定: sgn=+1 对应 exp(+2πi/N), sgn=-1 对应 exp(-2πi/N)
 */

#include <cmath>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <mpi.h>

using namespace std;

static const double PI = 3.141592653589793;

// ========== 前向声明 ==========
void cffti(int n, double w[]);
void cfft2_serial(int n, double x[], double y[], double w[], double sgn);
void step(int n, int mj, double a[], double b[], double c[],
          double d[], double w[], double sgn);
void ccopy(int n, double x[], double y[]);
double ggl(double *seed);
static inline double wall_time() { return MPI_Wtime(); }

// ========== FFT 核心例程 ==========
void cffti(int n, double w[]) {
    int n2 = n / 2;
    double aw = 2.0 * PI / n;
    for (int i = 0; i < n2; i++) {
        double arg = aw * i;
        w[i * 2] = cos(arg);
        w[i * 2 + 1] = sin(arg);
    }
}

void step(int n, int mj, double a[], double b[], double c[],
          double d[], double w[], double sgn) {
    int mj2 = 2 * mj, lj = n / mj2;
    for (int j = 0; j < lj; j++) {
        int jw = j * mj, ja = jw, jb = ja;
        int jc = j * mj2, jd = jc;
        double wr = w[jw * 2], wi = (sgn < 0.0) ? -w[jw * 2 + 1] : w[jw * 2 + 1];
        for (int k = 0; k < mj; k++) {
            int ak = (ja + k) * 2, bk = (jb + k) * 2;
            int ck = (jc + k) * 2, dk = (jd + k) * 2;
            c[ck] = a[ak] + b[bk];
            c[ck + 1] = a[ak + 1] + b[bk + 1];
            double ar = a[ak] - b[bk], ai = a[ak + 1] - b[bk + 1];
            d[dk] = wr * ar - wi * ai;
            d[dk + 1] = wr * ai + wi * ar;
        }
    }
}

void ccopy(int n, double x[], double y[]) {
    memcpy(y, x, 2 * n * sizeof(double));
}

void cfft2_serial(int n, double x[], double y[], double w[], double sgn) {
    int m = (int)(log((double)n) / log(1.99));
    int mj = 1, tgle = 1;
    step(n, mj, &x[0], &x[n], &y[0], &y[mj * 2], w, sgn);
    if (n == 2) return;
    for (int j = 0; j < m - 2; j++) {
        mj *= 2;
        if (tgle) {
            step(n, mj, &y[0], &y[n], &x[0], &x[mj * 2], w, sgn);
            tgle = 0;
        } else {
            step(n, mj, &x[0], &x[n], &y[0], &y[mj * 2], w, sgn);
            tgle = 1;
        }
    }
    if (tgle) ccopy(n, y, x);
    mj = n / 2;
    step(n, mj, &x[0], &x[n], &y[0], &y[mj * 2], w, sgn);
}

double ggl(double *seed) {
    const double d2 = 0.2147483647e10;
    double t = fmod(16807.0 * (*seed), d2);
    *seed = t;
    return (t - 1.0) / (d2 - 1.0);
}

// ========== MPI_Pack 优化的 Alltoall ==========
// 将 qpp 个复数 (连续存储) 序列化到 packed buffer，
// 使用 MPI_Alltoallv + MPI_PACKED 进行通信，
// 然后反序列化到目标缓冲区。
static void packed_alltoall(int qpp, const double src[], double dst[],
                            int P, MPI_Comm comm) {
    int dcount = 2 * qpp;  // 每个进程发送的 double 数量

    // 计算打包后的大小
    int pack_size;
    MPI_Pack_size(dcount, MPI_DOUBLE, comm, &pack_size);

    // 发送缓冲区: P 个连续块各自打包
    int send_total = P * (pack_size + MPI_BSEND_OVERHEAD);
    char *send_buf = new char[send_total];
    int position = 0;
    for (int p = 0; p < P; p++) {
        MPI_Pack(&src[p * dcount], dcount, MPI_DOUBLE,
                 send_buf, send_total, &position, comm);
    }

    // 接收缓冲区
    int recv_total = P * (pack_size + MPI_BSEND_OVERHEAD);
    char *recv_buf = new char[recv_total];

    // 每块大小: P 个进程各发送 sizeof(pack_size) 字节
    int *sendcounts = new int[P];
    int *recvcounts = new int[P];
    int *sdispls = new int[P];
    int *rdispls = new int[P];

    int block_size = position / P;  // 实际打包大小 (所有块相同)
    for (int p = 0; p < P; p++) {
        sendcounts[p] = block_size;
        recvcounts[p] = block_size;
        sdispls[p] = p * block_size;
        rdispls[p] = p * block_size;
    }

    MPI_Alltoallv(send_buf, sendcounts, sdispls, MPI_PACKED,
                  recv_buf, recvcounts, rdispls, MPI_PACKED, comm);

    // 反序列化
    position = 0;
    for (int p = 0; p < P; p++) {
        MPI_Unpack(recv_buf, recv_total, &position,
                   &dst[p * dcount], dcount, MPI_DOUBLE, comm);
    }

    delete[] send_buf;
    delete[] recv_buf;
    delete[] sendcounts;
    delete[] recvcounts;
    delete[] sdispls;
    delete[] rdispls;
}

// ========== 正变换 (使用 Packed Alltoall) ==========
static void forward_fft_opt(int Q, int P, int N,
                            double data[], double tmp[],
                            double w_Q[], double w_P[],
                            double *atobuf, double *colbuf,
                            int rank, MPI_Comm comm) {
    int qpp = Q / P;

    // Step 1: T (packed Alltoall)
    packed_alltoall(qpp, data, atobuf, P, comm);

    // Step 2: FFT_P(+1)
    {
        double *gbuf = new double[2 * P];
        double *fout = new double[2 * P];
        for (int k = 0; k < qpp; k++) {
            for (int p = 0; p < P; p++) {
                int src = 2 * (p * qpp + k);
                int dst = 2 * p;
                gbuf[dst]     = atobuf[src];
                gbuf[dst + 1] = atobuf[src + 1];
            }
            cfft2_serial(P, gbuf, fout, w_P, +1.0);
            for (int p = 0; p < P; p++) {
                int src = 2 * p;
                int dst = 2 * (p * qpp + k);
                colbuf[dst]     = fout[src];
                colbuf[dst + 1] = fout[src + 1];
            }
        }
        delete[] gbuf;
        delete[] fout;
    }

    // Step 3: twiddle W_N^{+ n2 * k1}
    for (int k = 0; k < qpp; k++) {
        int n2 = rank * qpp + k;
        for (int p = 0; p < P; p++) {
            double theta = 2.0 * PI * n2 * p / N;
            double wr = cos(theta), wi = sin(theta);
            int idx = 2 * (p * qpp + k);
            double re = colbuf[idx], im = colbuf[idx + 1];
            colbuf[idx]     = re * wr - im * wi;
            colbuf[idx + 1] = re * wi + im * wr;
        }
    }

    // Step 4: T (packed Alltoall)
    packed_alltoall(qpp, colbuf, tmp, P, comm);

    // Step 5: FFT_Q(+1)
    cfft2_serial(Q, tmp, data, w_Q, +1.0);
}

// ========== 逆变换 (使用 Packed Alltoall) ==========
static void inverse_fft_opt(int Q, int P, int N,
                            double data[], double tmp[],
                            double w_Q[], double w_P[],
                            double *atobuf, double *colbuf,
                            int rank, MPI_Comm comm) {
    int qpp = Q / P;

    // Step 1: FFT_Q(-1)
    cfft2_serial(Q, data, tmp, w_Q, -1.0);

    // Step 2: T (packed Alltoall)
    packed_alltoall(qpp, tmp, atobuf, P, comm);

    // Step 3: conj(twiddle) W_N^{- n2 * k1}
    for (int k = 0; k < qpp; k++) {
        int n2 = rank * qpp + k;
        for (int p = 0; p < P; p++) {
            double theta = -2.0 * PI * n2 * p / N;
            double wr = cos(theta), wi = sin(theta);
            int idx = 2 * (p * qpp + k);
            double re = atobuf[idx], im = atobuf[idx + 1];
            colbuf[idx]     = re * wr - im * wi;
            colbuf[idx + 1] = re * wi + im * wr;
        }
    }

    // Step 4: FFT_P(-1)
    {
        double *gbuf = new double[2 * P];
        double *fout = new double[2 * P];
        for (int k = 0; k < qpp; k++) {
            for (int p = 0; p < P; p++) {
                int src = 2 * (p * qpp + k);
                int dst = 2 * p;
                gbuf[dst]     = colbuf[src];
                gbuf[dst + 1] = colbuf[src + 1];
            }
            cfft2_serial(P, gbuf, fout, w_P, -1.0);
            for (int p = 0; p < P; p++) {
                int src = 2 * p;
                int dst = 2 * (p * qpp + k);
                colbuf[dst]     = fout[src];
                colbuf[dst + 1] = fout[src + 1];
            }
        }
        delete[] gbuf;
        delete[] fout;
    }

    // Step 5: T (packed Alltoall) + 除以 N
    packed_alltoall(qpp, colbuf, data, P, comm);

    double invN = 1.0 / (double)N;
    for (int i = 0; i < 2 * Q; i++) data[i] *= invN;
}

// ========== 主程序 ==========
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank, nprocs;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

    int ln2 = 16, nits = 100;
    if (argc > 1) ln2 = atoi(argv[1]);
    if (argc > 2) nits = atoi(argv[2]);

    int N = 1 << ln2;

    if (N % nprocs != 0) {
        if (rank == 0)
            cerr << "Error: N=" << N << " not divisible by P=" << nprocs << endl;
        MPI_Finalize(); return 1;
    }

    int Q = N / nprocs, P = nprocs;
    bool is_p1 = (P == 1);
    if (!is_p1 && Q % P != 0) {
        if (rank == 0)
            cerr << "Error: Q=N/P=" << Q << " not divisible by P=" << P
                 << " (P^2=" << P*P << " must divide N)" << endl;
        MPI_Finalize(); return 1;
    }

    int Q2 = 2 * Q, total_N2 = 2 * N;

    double *data   = new double[Q2];
    double *tmp    = new double[Q2];
    double *atobuf = new double[Q2];
    double *colbuf = new double[Q2];
    double *w_Q    = new double[Q2];
    double *w_P    = new double[2 * P];

    double *global_x = nullptr, *global_z = nullptr;
    if (rank == 0) {
        global_x = new double[total_N2];
        global_z = new double[total_N2];
    }

    // 初始化
    double seed = 331.0;
    if (rank == 0) {
        for (int i = 0; i < total_N2; i += 2) {
            double z0 = ggl(&seed), z1 = ggl(&seed);
            global_x[i] = z0; global_x[i + 1] = z1;
            global_z[i] = z0; global_z[i + 1] = z1;
        }
    }
    MPI_Scatter(global_x, Q2, MPI_DOUBLE,
                data, Q2, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    cffti(Q, w_Q);
    cffti(P, w_P);

    // ---- 计时 ----
    MPI_Barrier(MPI_COMM_WORLD);
    double t_start = wall_time();

    for (int it = 0; it < nits; it++) {
        if (is_p1) {
            cfft2_serial(Q, data, tmp, w_Q, +1.0);
            double invN = 1.0 / (double)N;
            cfft2_serial(Q, tmp, data, w_Q, -1.0);
            for (int i = 0; i < Q2; i++) data[i] *= invN;
        } else {
            forward_fft_opt(Q, P, N, data, tmp, w_Q, w_P,
                            atobuf, colbuf, rank, MPI_COMM_WORLD);
            inverse_fft_opt(Q, P, N, data, tmp, w_Q, w_P,
                            atobuf, colbuf, rank, MPI_COMM_WORLD);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double elapsed = wall_time() - t_start;

    // 收集结果
    double *result_x = nullptr;
    if (rank == 0) result_x = new double[total_N2];
    MPI_Gather(data, Q2, MPI_DOUBLE,
               result_x, Q2, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        double error = 0.0;
        for (int i = 0; i < total_N2; i += 2) {
            double dr = result_x[i] - global_z[i];
            double di = result_x[i + 1] - global_z[i + 1];
            error += dr * dr + di * di;
        }
        error = sqrt(error / (double)N);

        double flops = 2.0 * nits * (5.0 * (double)N * (double)ln2);
        double mflops = flops / 1.0E+06 / elapsed;

        cout << "FFT_MPI_RESULT:"
             << " N=" << N << " P=" << nprocs << " nits=" << nits
             << " error=" << scientific << setprecision(6) << error
             << " time=" << fixed << setprecision(6) << elapsed
             << " mflops=" << fixed << setprecision(2) << mflops
             << endl;
    }

    delete[] data; delete[] tmp; delete[] atobuf; delete[] colbuf;
    delete[] w_Q; delete[] w_P;
    if (rank == 0) { delete[] global_x; delete[] global_z; delete[] result_x; }

    MPI_Finalize();
    return 0;
}
