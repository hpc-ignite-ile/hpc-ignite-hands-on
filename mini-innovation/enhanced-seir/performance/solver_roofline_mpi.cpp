#include <mpi.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

struct Args {
    int n_global = 1200000;
    int iters = 180;
    std::string label = "jacobi";
};

Args parse_args(int argc, char** argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];
        if (key == "--n" && i + 1 < argc) {
            args.n_global = std::atoi(argv[++i]);
        } else if (key == "--iters" && i + 1 < argc) {
            args.iters = std::atoi(argv[++i]);
        } else if (key == "--label" && i + 1 < argc) {
            args.label = argv[++i];
        }
    }
    return args;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank = 0;
    int size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    Args args = parse_args(argc, argv);

    const int base = args.n_global / size;
    const int rem = args.n_global % size;
    const int n_local = base + (rank < rem ? 1 : 0);
    std::vector<double> x(n_local + 2, 0.0);
    std::vector<double> y(n_local + 2, 0.0);
    std::vector<double> rhs(n_local + 2, 1.0);

    const int left = rank == 0 ? MPI_PROC_NULL : rank - 1;
    const int right = rank == size - 1 ? MPI_PROC_NULL : rank + 1;
    double local_residual = 0.0;

    MPI_Barrier(MPI_COMM_WORLD);
    const double t0 = MPI_Wtime();
    for (int it = 0; it < args.iters; ++it) {
        MPI_Sendrecv(&x[1], 1, MPI_DOUBLE, left, 10, &x[n_local + 1], 1, MPI_DOUBLE, right, 10, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Sendrecv(&x[n_local], 1, MPI_DOUBLE, right, 20, &x[0], 1, MPI_DOUBLE, left, 20, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

        double sumsq = 0.0;
        for (int i = 1; i <= n_local; ++i) {
            y[i] = 0.5 * (x[i - 1] + x[i + 1] - rhs[i]);
            const double r = y[i] - x[i];
            sumsq += r * r;
        }
        x.swap(y);
        if ((it + 1) % 20 == 0 || it + 1 == args.iters) {
            MPI_Allreduce(&sumsq, &local_residual, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
        }
    }
    const double local_elapsed = MPI_Wtime() - t0;

    double elapsed = 0.0;
    MPI_Reduce(&local_elapsed, &elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    const double local_flops = static_cast<double>(n_local) * args.iters * 8.0;
    const double local_bytes = static_cast<double>(n_local) * args.iters * 5.0 * sizeof(double);
    double flops = 0.0;
    double bytes = 0.0;
    MPI_Reduce(&local_flops, &flops, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_bytes, &bytes, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        const double point_rate = static_cast<double>(args.n_global) * args.iters / std::max(elapsed, 1e-12);
        const double gflops = flops / std::max(elapsed, 1e-12) / 1e9;
        const double gbps = bytes / std::max(elapsed, 1e-12) / 1e9;
        const double ai = flops / std::max(bytes, 1.0);
        std::cout << std::fixed << std::setprecision(6)
                  << args.label << "," << size << "," << args.n_global << "," << args.iters << ","
                  << elapsed << "," << point_rate << "," << gflops << "," << gbps << "," << ai << ","
                  << std::sqrt(local_residual) << "\n";
    }

    MPI_Finalize();
    return 0;
}
