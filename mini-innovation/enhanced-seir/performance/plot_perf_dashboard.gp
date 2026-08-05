set datafile separator ","
set terminal pngcairo size 1800,1200 enhanced font "Arial,12"
set output "figures/perf_workshop_dashboard.png"

summary_csv = "results/perf_workshop_summary.csv"
theory_csv = "results/amdahl_gustafson.csv"
python_csv = "results/python_stack_overhead.csv"
solver_csv = system("ls -t results/solver_roofline_*.csv 2>/dev/null | head -1")
if (strlen(solver_csv) == 0) solver_csv = "results/solver_roofline_latest.csv"

set print "results/perf_workshop_gnuplot_summary.txt"
print "dashboard=figures/perf_workshop_dashboard.png"
print "summary_csv=".summary_csv
print "theory_csv=".theory_csv
print "solver_csv=".solver_csv
print "python_csv=".python_csv
set print

set style line 1 lc rgb "#2563eb" lw 3 pt 7 ps 1.1
set style line 2 lc rgb "#94a3b8" lw 2 dt 2
set style line 3 lc rgb "#7c3aed" lw 3 pt 5 ps 1.1
set style line 4 lc rgb "#0f766e" lw 2 pt 9 ps 1.1
set style line 5 lc rgb "#dc2626" lw 2 pt 11 ps 1.1
set style fill solid 0.82 border rgb "#374151"
set boxwidth 0.65
set grid
set key outside right top

set multiplot layout 2,3 title "Enhanced SEIR Performance Evaluation Dashboard"

set title "MPI Solver Speedup"
set xlabel "MPI ranks"
set ylabel "speedup"
set yrange [0:*]
plot summary_csv every ::1 using 1:3 with linespoints ls 1 title "observed", \
     summary_csv every ::1 using 1:1 with lines ls 2 title "ideal"

set title "Efficiency and Serial Fraction"
set xlabel "MPI ranks"
set ylabel "fraction"
set yrange [0:1.1]
plot summary_csv every ::1 using 1:4 with linespoints ls 3 title "efficiency", \
     summary_csv every ::1 using 1:6 with linespoints ls 5 title "Karp-Flatt serial"

set title "Estimated Overhead"
set xlabel "MPI ranks"
set ylabel "seconds"
set yrange [0:*]
set style data boxes
plot summary_csv every ::1 using 1:5 with boxes lc rgb "#0f766e" title "overhead_sec"
set style data linespoints

set title "Roofline Signal from Solver"
set xlabel "observed GB/s"
set ylabel "observed GFLOP/s"
set yrange [0:*]
plot solver_csv every ::1 using 8:7 with linespoints ls 4 title "bandwidth vs flops", \
     solver_csv every ::1 using 8:7:2 with labels offset 1,1 title "ranks"

set title "Amdahl and Gustafson, f=0.08"
set xlabel "workers"
set ylabel "speedup"
set yrange [0:*]
plot theory_csv every ::1 using 1:(strcol(2) eq "0.08" ? $3 : 1/0) with linespoints ls 1 title "Amdahl", \
     theory_csv every ::1 using 1:(strcol(2) eq "0.08" ? $4 : 1/0) with linespoints ls 4 title "Gustafson"

set title "Python Stack Cost"
set xlabel "case"
set ylabel "seconds"
set xtics rotate by -35 right
set yrange [0:*]
set style data histograms
plot python_csv every ::1 using 2:xtic(1) lc rgb "#f59e0b" title "elapsed_sec"
set style data linespoints
set xtics norotate

unset multiplot

set terminal pngcairo size 1100,720 enhanced font "Arial,12"
set output "figures/perf_workshop_speedup_efficiency.png"
set title "Enhanced SEIR Performance Summary"
set xlabel "MPI ranks"
set ylabel "speedup / efficiency"
set yrange [0:*]
plot summary_csv every ::1 using 1:3 with linespoints ls 1 title "speedup", \
     summary_csv every ::1 using 1:4 with linespoints ls 3 title "efficiency", \
     summary_csv every ::1 using 1:1 with lines ls 2 title "ideal speedup"

set output "figures/perf_workshop_python_stack.png"
set title "Python Stack Cost"
set xlabel "case"
set ylabel "seconds"
set xtics rotate by -35 right
set style data histograms
plot python_csv every ::1 using 2:xtic(1) lc rgb "#f59e0b" title "elapsed_sec"
