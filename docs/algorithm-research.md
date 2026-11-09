# Algorithm Research Pilot — Simulated Bifurcation and FG-dSB

## Candidate selection

The current QUBO interface can support CPU experiments without adding a
dependency. Published simulated bifurcation (SB) maps an Ising objective to
coupled classical oscillator dynamics. Discrete SB (dSB) uses the signs of
neighbor positions in its interaction force; its symplectic-Euler updates can
be implemented as a deterministic, seeded Python reference. This makes dSB a
realistic ARC-07 candidate, not evidence that it will outperform other methods.

The literature already contains standard dSB variants and tabu-enhanced SB.
Accordingly, this pilot does not claim that dSB or tabu search is our invention.
Our project-specific experiment, **Feasibility-Guided dSB (FG-dSB)**, tests a
small hybrid: dSB proposes a QUBO state; a deterministic local repair ranks
one- and two-decision-bit changes by (1) number of violated original
constraints, (2) normalized total violation, and (3) the original objective;
integer slack bits are then re-encoded and the result is checked against the
original constraints. This is an engineering hypothesis, not a novelty claim or
proof of global optimality.

## Implemented pilot

`examples/qubo_heuristics.py` contains a CPU dSB reference and FG-dSB. The
Ising/QUBO mapping is tested by comparing energies for all states of a small
fixture. `examples/bifurcation_experiment.py` compares simulated annealing,
dSB, FG-dSB, and exact QUBO enumeration on the three existing synthetic cases.
It records paired fixed-seed solution-quality and runtime results. Infeasible
original problems remain labelled infeasible; a QUBO penalty minimum is never
reported as a feasible solution unless the original constraints pass.

The default pilot uses only three tiny cases and three seeds so it is quick to
reproduce. It validates interfaces and exposes obvious failures; it is far too
small to support a world-class performance claim. For meaningful evaluation,
next add multiple generated QUBO families, size/density sweeps, more paired
seeds, parameter sensitivity, time-to-target distributions, and an independent
implementation or reference solver. Report solution quality and wall-clock
cost together; do not tune on the final test instances.

## 20-seed pilot observations

The comparison was also run with seeds 0–19 on each existing eight-bit synthetic
QUBO. The table gives exact-QUBO-energy hit rate and mean runtime in milliseconds
for one fixed configuration on one WSL CPU environment.

| Case | Simulated annealing | dSB | FG-dSB | Exact QUBO enumeration |
| --- | ---: | ---: | ---: | ---: |
| Feasible | 10/20 (50%); 27.7 ms | 15/20 (75%); 21.6 ms | 20/20 (100%); 24.8 ms | 20/20 (100%); 4.4 ms |
| Resource-constrained | 11/20 (55%); 25.0 ms | 15/20 (75%); 20.3 ms | 15/20 (75%); 19.6 ms | 20/20 (100%); 2.6 ms |
| Infeasible | 18/20 (90%); 24.6 ms | 14/20 (70%); 20.5 ms | 20/20 (100%); 21.4 ms | 20/20 (100%); 2.6 ms |

All methods returned feasible assignments on every run for the two feasible
cases. All returned infeasible assignments for the contradictory case; the
reported 90%/70%/100% rates there mean “matched the exact minimum QUBO energy,”
not that a feasible solution was found. On these tiny instances exact enumeration
was faster, so this pilot shows no performance advantage. It only indicates that
the FG-dSB repair can improve exact-energy hit rate on some of these fixed
fixtures. One synthetic family and 20 seeds are not enough to establish
generalization, significance, or literature novelty.

## Run

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/bifurcation_experiment.py --seeds 0,1,2
```

## Sources

- Goto, Tatsumura, and Dixon, [Combinatorial optimization by simulating adiabatic bifurcations in nonlinear Hamiltonian systems](https://doi.org/10.1126/sciadv.aav2372), *Science Advances* (2019).
- Goto and Tatsumura, [Large-Scale Combinatorial Optimization based on Simulated Bifurcation Algorithm](https://search.ieice.org/bin/summary.php?abst=j&category=C&id=j104-c_4_110&lang=1&year=2021), *IEICE Transactions* (2021).
- Oshiyama et al., [Benchmark of quantum-inspired heuristic solvers for QUBO](https://doi.org/10.1038/s41598-022-06070-5), *Scientific Reports* (2022).
- Tao et al., [Tabu-Enhanced Simulated Bifurcation for combinatorial optimization](https://doi.org/10.1038/s42005-026-02538-2), *Communications Physics* (2026).
