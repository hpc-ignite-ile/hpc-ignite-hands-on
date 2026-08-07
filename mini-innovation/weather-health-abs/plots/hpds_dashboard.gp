set datafile separator ","
set terminal pngcairo size 1200,760 enhanced font "Arial,12"
set output "figures/hpds_weather_abs_gnuplot.png"
csv = "results/hpds_policy_summary.csv"
set style fill solid 0.85 border rgb "#334155"
set grid ytics
set multiplot layout 2,2 title "Weather-Health ABS HPDS Dashboard"
set title "Heat Index"
set ylabel "C"
set style data histograms
set xtics rotate by -25 right
plot csv every ::1 using 2:xtic(1) lc rgb "#2563eb" title "mean max"
set title "Exposure"
set ylabel "agent-hours"
plot csv every ::1 using 3:xtic(1) lc rgb "#dc2626" title "exposure"
set title "Cooling"
set ylabel "kWh proxy"
plot csv every ::1 using 4:xtic(1) lc rgb "#0f766e" title "cooling"
set title "Risk Proxy"
set ylabel "risk"
plot csv every ::1 using 5:xtic(1) lc rgb "#7c3aed" title "risk"
unset multiplot
