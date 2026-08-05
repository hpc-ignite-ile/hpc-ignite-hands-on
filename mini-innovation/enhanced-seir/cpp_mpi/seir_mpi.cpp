#include <mpi.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kAges = 4;
constexpr double kPi = 3.14159265358979323846;

struct Patch {
    int id = 0;
    std::string name;
    std::array<double, kAges> population{};
    double initial_exposed = 0.0;
    double initial_infectious = 0.0;
};

struct Scenario {
    int id = 0;
    std::string policy;
    double beta_scale = 1.0;
    double mobility_scale = 0.2;
    double vaccination_rate = 0.0;
    double contact_reduction = 1.0;
    int days = 80;
    unsigned long seed = 20260805;
};

struct Summary {
    int scenario_id = 0;
    int rank = 0;
    int days = 0;
    char policy[40]{};
    double elapsed_sec = 0.0;
    double total_population = 0.0;
    double peak_infectious = 0.0;
    double peak_hospitalized = 0.0;
    double attack_rate = 0.0;
    double final_deaths = 0.0;
    double final_recovered = 0.0;
};

std::string trim(const std::string& s) {
    const auto first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return "";
    const auto last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

std::vector<std::string> split_csv(const std::string& line) {
    std::vector<std::string> out;
    std::stringstream ss(line);
    std::string item;
    while (std::getline(ss, item, ',')) out.push_back(trim(item));
    return out;
}

std::map<std::string, int> header_index(const std::vector<std::string>& header) {
    std::map<std::string, int> index;
    for (int i = 0; i < static_cast<int>(header.size()); ++i) index[header[i]] = i;
    return index;
}

double get_double(const std::vector<std::string>& row, const std::map<std::string, int>& idx, const std::string& key) {
    const auto it = idx.find(key);
    if (it == idx.end() || it->second >= static_cast<int>(row.size())) {
        throw std::runtime_error("missing CSV column: " + key);
    }
    return std::stod(row[it->second]);
}

int get_int(const std::vector<std::string>& row, const std::map<std::string, int>& idx, const std::string& key) {
    return static_cast<int>(std::llround(get_double(row, idx, key)));
}

std::string get_string(const std::vector<std::string>& row, const std::map<std::string, int>& idx, const std::string& key) {
    const auto it = idx.find(key);
    if (it == idx.end() || it->second >= static_cast<int>(row.size())) {
        throw std::runtime_error("missing CSV column: " + key);
    }
    return row[it->second];
}

std::vector<Patch> read_patches(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open patches file: " + path);
    std::string line;
    std::getline(in, line);
    const auto idx = header_index(split_csv(line));
    std::vector<Patch> patches;
    while (std::getline(in, line)) {
        if (trim(line).empty()) continue;
        const auto row = split_csv(line);
        Patch p;
        p.id = get_int(row, idx, "patch_id");
        p.name = get_string(row, idx, "name");
        p.population = {
            get_double(row, idx, "pop_0_19"),
            get_double(row, idx, "pop_20_39"),
            get_double(row, idx, "pop_40_64"),
            get_double(row, idx, "pop_65_plus"),
        };
        p.initial_exposed = get_double(row, idx, "initial_exposed");
        p.initial_infectious = get_double(row, idx, "initial_infectious");
        patches.push_back(p);
    }
    return patches;
}

std::vector<double> read_contact_matrix(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open contact file: " + path);
    std::string line;
    std::getline(in, line);
    std::vector<double> matrix(kAges * kAges, 0.0);
    int row_id = 0;
    while (std::getline(in, line) && row_id < kAges) {
        if (trim(line).empty()) continue;
        const auto row = split_csv(line);
        for (int a = 0; a < kAges; ++a) matrix[row_id * kAges + a] = std::stod(row[a + 1]);
        ++row_id;
    }
    return matrix;
}

std::vector<double> read_mobility(const std::string& path, int patches) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open mobility file: " + path);
    std::string line;
    std::getline(in, line);
    const auto idx = header_index(split_csv(line));
    std::vector<double> mobility(patches * patches, 0.0);
    while (std::getline(in, line)) {
        if (trim(line).empty()) continue;
        const auto row = split_csv(line);
        const int from = get_int(row, idx, "from_patch");
        const int to = get_int(row, idx, "to_patch");
        if (from >= 0 && from < patches && to >= 0 && to < patches) {
            mobility[from * patches + to] = get_double(row, idx, "weight");
        }
    }
    for (int p = 0; p < patches; ++p) {
        double row_sum = 0.0;
        for (int q = 0; q < patches; ++q) row_sum += mobility[p * patches + q];
        if (row_sum <= 0.0) mobility[p * patches + p] = 1.0;
        else for (int q = 0; q < patches; ++q) mobility[p * patches + q] /= row_sum;
    }
    return mobility;
}

std::vector<Scenario> read_scenarios(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open scenarios file: " + path);
    std::string line;
    std::getline(in, line);
    const auto idx = header_index(split_csv(line));
    std::vector<Scenario> scenarios;
    while (std::getline(in, line)) {
        if (trim(line).empty()) continue;
        const auto row = split_csv(line);
        Scenario s;
        s.id = get_int(row, idx, "scenario_id");
        s.policy = get_string(row, idx, "policy");
        s.beta_scale = get_double(row, idx, "beta_scale");
        s.mobility_scale = get_double(row, idx, "mobility_scale");
        s.vaccination_rate = get_double(row, idx, "vaccination_rate");
        s.contact_reduction = get_double(row, idx, "contact_reduction");
        s.days = get_int(row, idx, "days");
        s.seed += static_cast<unsigned long>(s.id * 1009);
        scenarios.push_back(s);
    }
    return scenarios;
}

struct State {
    std::vector<double> S, V, E, Ip, Ia, Is, H, R, D, N;
};

void scale_pair(double& x, double& y, double cap) {
    const double total = x + y;
    if (total > cap && total > 0.0) {
        const double factor = cap / total;
        x *= factor;
        y *= factor;
    }
}

Summary simulate(const Scenario& scenario, const std::vector<Patch>& patches, const std::vector<double>& mobility,
                 const std::vector<double>& contact, int rank, int days_override) {
    const double start = MPI_Wtime();
    const int P = static_cast<int>(patches.size());
    const int cells = P * kAges;
    const int days = days_override > 0 ? days_override : scenario.days;

    const std::array<double, kAges> susceptibility{0.75, 1.00, 1.08, 0.90};
    const std::array<double, kAges> asymptomatic_prob{0.42, 0.34, 0.26, 0.20};
    const std::array<double, kAges> hospital_prob{0.006, 0.014, 0.045, 0.135};
    const std::array<double, kAges> fatality_prob{0.0003, 0.0010, 0.0080, 0.0450};

    State x;
    x.S.assign(cells, 0.0);
    x.V.assign(cells, 0.0);
    x.E.assign(cells, 0.0);
    x.Ip.assign(cells, 0.0);
    x.Ia.assign(cells, 0.0);
    x.Is.assign(cells, 0.0);
    x.H.assign(cells, 0.0);
    x.R.assign(cells, 0.0);
    x.D.assign(cells, 0.0);
    x.N.assign(cells, 0.0);

    double total_pop = 0.0;
    for (int p = 0; p < P; ++p) {
        const double patch_pop = std::accumulate(patches[p].population.begin(), patches[p].population.end(), 0.0);
        for (int a = 0; a < kAges; ++a) {
            const int c = p * kAges + a;
            const double frac = patch_pop > 0.0 ? patches[p].population[a] / patch_pop : 0.0;
            const double e0 = patches[p].initial_exposed * frac;
            const double i0 = patches[p].initial_infectious * frac;
            x.N[c] = patches[p].population[a];
            x.S[c] = std::max(0.0, patches[p].population[a] - e0 - i0);
            x.E[c] = e0;
            x.Is[c] = i0;
            total_pop += patches[p].population[a];
        }
    }

    std::mt19937_64 rng(scenario.seed);
    std::normal_distribution<double> beta_noise(1.0, 0.015);

    double cumulative_infections = 0.0;
    double peak_infectious = 0.0;
    double peak_hospital = 0.0;
    const double beta0 = 0.055;
    const double sigma = 1.0 / 3.0;
    const double presym_rate = 1.0 / 2.0;
    const double rec_a = 1.0 / 5.5;
    const double rec_s = 1.0 / 6.5;
    const double hosp_rate = 1.0 / 5.0;
    const double hosp_recover = 1.0 / 9.0;
    const double hosp_die = 1.0 / 12.0;
    const double vaccine_efficacy_infection = 0.62;

    for (int day = 0; day < days; ++day) {
        std::vector<double> prevalence(cells, 0.0);
        for (int c = 0; c < cells; ++c) {
            const double infectious = 0.65 * x.Ip[c] + 0.45 * x.Ia[c] + x.Is[c] + 0.08 * x.H[c];
            prevalence[c] = x.N[c] > 1.0 ? infectious / x.N[c] : 0.0;
        }

        std::vector<double> newE(cells, 0.0), newIp(cells, 0.0), newIa(cells, 0.0), newIs(cells, 0.0);
        std::vector<double> newH(cells, 0.0), newRa(cells, 0.0), newRs(cells, 0.0), newRh(cells, 0.0), newD(cells, 0.0), newV(cells, 0.0);

        const double seasonality = 1.0 + 0.10 * std::cos(2.0 * kPi * static_cast<double>(day - 15) / 365.0);
        const double daily_beta = beta0 * scenario.beta_scale * scenario.contact_reduction * seasonality *
                                  std::clamp(beta_noise(rng), 0.94, 1.06);

        for (int p = 0; p < P; ++p) {
            std::array<double, kAges> mixed_prev{};
            for (int a = 0; a < kAges; ++a) {
                double imported = 0.0;
                for (int q = 0; q < P; ++q) imported += mobility[p * P + q] * prevalence[q * kAges + a];
                mixed_prev[a] = (1.0 - scenario.mobility_scale) * prevalence[p * kAges + a] +
                                scenario.mobility_scale * imported;
            }
            for (int a = 0; a < kAges; ++a) {
                const int c = p * kAges + a;
                double contact_force = 0.0;
                for (int b = 0; b < kAges; ++b) contact_force += contact[a * kAges + b] * mixed_prev[b];
                const double lambda = std::clamp(daily_beta * susceptibility[a] * contact_force, 0.0, 0.85);
                const double inf_s = std::min(x.S[c], lambda * x.S[c]);
                const double inf_v = std::min(x.V[c], lambda * (1.0 - vaccine_efficacy_infection) * x.V[c]);
                newE[c] = inf_s + inf_v;
                newV[c] = std::min(x.S[c] - inf_s, scenario.vaccination_rate * x.S[c]);
            }
        }

        for (int c = 0; c < cells; ++c) {
            const int a = c % kAges;
            newIp[c] = std::min(x.E[c], sigma * x.E[c]);
            const double leaving_presym = std::min(x.Ip[c], presym_rate * x.Ip[c]);
            newIa[c] = leaving_presym * asymptomatic_prob[a];
            newIs[c] = leaving_presym - newIa[c];
            newRa[c] = std::min(x.Ia[c], rec_a * x.Ia[c]);
            newH[c] = std::min(x.Is[c], hospital_prob[a] * hosp_rate * x.Is[c]);
            newRs[c] = std::min(x.Is[c], (1.0 - hospital_prob[a]) * rec_s * x.Is[c]);
            scale_pair(newH[c], newRs[c], x.Is[c]);
            newD[c] = std::min(x.H[c], fatality_prob[a] * hosp_die * x.H[c]);
            newRh[c] = std::min(x.H[c], (1.0 - fatality_prob[a]) * hosp_recover * x.H[c]);
            scale_pair(newD[c], newRh[c], x.H[c]);
        }

        double infectious_today = 0.0;
        double hospital_today = 0.0;
        for (int c = 0; c < cells; ++c) {
            x.S[c] = std::max(0.0, x.S[c] - newE[c] - newV[c]);
            x.V[c] = std::max(0.0, x.V[c] + newV[c] - 0.0);
            x.E[c] = std::max(0.0, x.E[c] + newE[c] - newIp[c]);
            x.Ip[c] = std::max(0.0, x.Ip[c] + newIp[c] - newIa[c] - newIs[c]);
            x.Ia[c] = std::max(0.0, x.Ia[c] + newIa[c] - newRa[c]);
            x.Is[c] = std::max(0.0, x.Is[c] + newIs[c] - newH[c] - newRs[c]);
            x.H[c] = std::max(0.0, x.H[c] + newH[c] - newD[c] - newRh[c]);
            x.R[c] += newRa[c] + newRs[c] + newRh[c];
            x.D[c] += newD[c];
            x.N[c] = std::max(1.0, x.S[c] + x.V[c] + x.E[c] + x.Ip[c] + x.Ia[c] + x.Is[c] + x.H[c] + x.R[c]);
            cumulative_infections += newE[c];
            infectious_today += x.Ip[c] + x.Ia[c] + x.Is[c];
            hospital_today += x.H[c];
        }
        peak_infectious = std::max(peak_infectious, infectious_today);
        peak_hospital = std::max(peak_hospital, hospital_today);
    }

    double deaths = std::accumulate(x.D.begin(), x.D.end(), 0.0);
    double recovered = std::accumulate(x.R.begin(), x.R.end(), 0.0);

    Summary summary;
    summary.scenario_id = scenario.id;
    summary.rank = rank;
    summary.days = days;
    std::strncpy(summary.policy, scenario.policy.c_str(), sizeof(summary.policy) - 1);
    summary.elapsed_sec = MPI_Wtime() - start;
    summary.total_population = total_pop;
    summary.peak_infectious = peak_infectious;
    summary.peak_hospitalized = peak_hospital;
    summary.attack_rate = total_pop > 0.0 ? cumulative_infections / total_pop : 0.0;
    summary.final_deaths = deaths;
    summary.final_recovered = recovered;
    return summary;
}

std::string arg_value(int argc, char** argv, const std::string& name, const std::string& fallback) {
    for (int i = 1; i + 1 < argc; ++i) {
        if (argv[i] == name) return argv[i + 1];
    }
    return fallback;
}

int arg_int(int argc, char** argv, const std::string& name, int fallback) {
    return std::stoi(arg_value(argc, argv, name, std::to_string(fallback)));
}

}  // namespace

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank = 0;
    int size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    try {
        const std::string scenario_file = arg_value(argc, argv, "--scenario-file", "data/scenarios.csv");
        const std::string patches_file = arg_value(argc, argv, "--patches", "data/patches.csv");
        const std::string mobility_file = arg_value(argc, argv, "--mobility", "data/mobility.csv");
        const std::string contact_file = arg_value(argc, argv, "--contact", "data/age_contact_4x4.csv");
        const std::string output_file = arg_value(argc, argv, "--out", "results/seir_mpi_summary.csv");
        const int days_override = arg_int(argc, argv, "--days", -1);

        const auto patches = read_patches(patches_file);
        const auto mobility = read_mobility(mobility_file, static_cast<int>(patches.size()));
        const auto contact = read_contact_matrix(contact_file);
        const auto scenarios = read_scenarios(scenario_file);

        std::vector<Summary> local;
        for (int i = rank; i < static_cast<int>(scenarios.size()); i += size) {
            local.push_back(simulate(scenarios[i], patches, mobility, contact, rank, days_override));
        }

        const int local_bytes = static_cast<int>(local.size() * sizeof(Summary));
        std::vector<int> counts(size, 0);
        MPI_Gather(&local_bytes, 1, MPI_INT, counts.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);

        std::vector<int> displs(size, 0);
        int total_bytes = 0;
        if (rank == 0) {
            for (int i = 0; i < size; ++i) {
                displs[i] = total_bytes;
                total_bytes += counts[i];
            }
        }

        std::vector<Summary> gathered;
        if (rank == 0) gathered.resize(total_bytes / static_cast<int>(sizeof(Summary)));
        MPI_Gatherv(local.data(), local_bytes, MPI_BYTE, gathered.data(), counts.data(), displs.data(), MPI_BYTE, 0, MPI_COMM_WORLD);

        if (rank == 0) {
            std::sort(gathered.begin(), gathered.end(), [](const Summary& a, const Summary& b) {
                return a.scenario_id < b.scenario_id;
            });
            std::ofstream out(output_file);
            out << "scenario_id,policy,rank,days,elapsed_sec,total_population,peak_infectious,peak_hospitalized,attack_rate,final_deaths,final_recovered\n";
            out << std::fixed << std::setprecision(6);
            for (const auto& s : gathered) {
                out << s.scenario_id << ',' << s.policy << ',' << s.rank << ',' << s.days << ',' << s.elapsed_sec << ','
                    << s.total_population << ',' << s.peak_infectious << ',' << s.peak_hospitalized << ',' << s.attack_rate
                    << ',' << s.final_deaths << ',' << s.final_recovered << '\n';
            }
            std::cout << "wrote " << output_file << " with " << gathered.size() << " scenario summaries\n";
        }
    } catch (const std::exception& exc) {
        std::cerr << "rank " << rank << " error: " << exc.what() << "\n";
        MPI_Abort(MPI_COMM_WORLD, 2);
    }

    MPI_Finalize();
    return 0;
}
