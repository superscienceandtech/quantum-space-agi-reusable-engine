# QUBO Generalization Benchmark

## Purpose

This benchmark checks whether the existing solver comparison behaves
consistently beyond the original three tiny fixtures. It generates deterministic
instances from three families:

- Sparse weighted Max-Cut.
- Dense weighted Max-Cut.
- 0/1 knapsack with one capacity constraint.

The default sweep uses 8, 12, and 16 decision variables, three independently
generated instances per family/size setting, and 30 paired solver seeds per
instance. This gives 90 heuristic runs per family/size/method cell.

## Compared methods

- Exact enumeration is the reference oracle for the original decision problem.
  Its runtime and evaluated-candidate count are reported separately; it does
  not receive the heuristic evaluation budget.
- Simulated Annealing and discrete Simulated Bifurcation receive a requested
  budget of 1,024 QUBO energy evaluations per run. Their actual counts are
  included in the report.
- Feasibility-Guided dSB is run on knapsack instances. Its dSB search receives
  the same base budget; additional repair candidates and total runtime are
  disclosed separately.
- QAOA is not mixed into these CPU heuristic budgets. The existing Qiskit
  StatevectorSampler experiment remains a separate ideal local-simulator study.

## Metrics

For every method and instance, the JSON report includes feasibility rate,
exact-original-objective hit rate, mean and median optimality gap, relative gap,
wall-clock runtime, and evaluation counts. Solver seeds are paired across
methods. Max-Cut objective is cut weight; knapsack objective is total value.

## Measured 30-seed pilot

Run in the WSL environment. Each table row aggregates 90 heuristic runs
(three generated instances times 30 solver seeds). Heuristic cells show
exact-objective hit rate, mean objective gap, and median runtime. Exact timing
is the mean over its three instance-level oracle runs.

| Family | Variables | Exact oracle mean time | Simulated Annealing | dSB | FG-dSB |
| --- | ---: | ---: | --- | --- | --- |
| Sparse Max-Cut | 8 | 1.3 ms | 100%; 0.000; 5.6 ms | 100%; 0.000; 16.1 ms | — |
| Sparse Max-Cut | 12 | 26.8 ms | 93.3%; 0.078; 8.0 ms | 100%; 0.000; 27.3 ms | — |
| Sparse Max-Cut | 16 | 564.1 ms | 74.4%; 1.011; 10.5 ms | 90.0%; 0.256; 41.9 ms | — |
| Dense Max-Cut | 8 | 1.5 ms | 100%; 0.000; 7.2 ms | 98.9%; 0.011; 17.9 ms | — |
| Dense Max-Cut | 12 | 37.8 ms | 88.9%; 0.200; 12.3 ms | 96.7%; 0.111; 32.0 ms | — |
| Dense Max-Cut | 16 | 986.6 ms | 84.4%; 0.700; 18.7 ms | 87.8%; 0.589; 52.4 ms | — |
| Knapsack | 8 | 6.2 ms | 1.1%; 53.567; 18.6 ms | 2.2%; 39.911; 44.9 ms | 90.0%; 0.911; 45.6 ms |
| Knapsack | 12 | 37.7 ms | 0%; 80.378; 30.6 ms | 0%; 65.433; 73.1 ms | 76.7%; 4.167; 75.4 ms |
| Knapsack | 16 | 897.7 ms | 0%; 95.689; 46.4 ms | 0%; 74.382; 111.8 ms | 13.3%; 5.100; 120.0 ms |

All methods returned feasible solutions on all Max-Cut runs. Knapsack
feasibility was 100% except dSB at 16 variables, which was 98.9%. On these
generated Max-Cut cases, dSB and simulated annealing often found the exact
optimum, with different rates by density and size. On knapsack, FG-dSB repair
reduced the mean objective gap relative to the two un-repaired heuristics, but
its exact-hit rate fell to 13.3% at 16 variables. Runtime comparisons also
depend on size: exhaustive search was often faster on small cases, while at 16
variables it was slower but guaranteed the exact reference. These results are
family-dependent and do not establish general solver superiority.

The benchmark uses only three generated instances per family/size. It is a
reproducible exploratory study, not a statistical survey of the problem
distribution. Timings depend on the host. Equal energy-evaluation counts
approximate search work, not equal CPU instructions. No quantum advantage or
global novelty claim is made.

## Public Max-Cut reference comparison

The existing Ising JSON loader was exercised on all four instances listed in
Kipu Quantum's public benchmark repository. Its README describes the format and
publishes ground-state energy references; this project treats these as
upstream references, not independently certified optima. No `EnumerativeSolver`
result is claimed: even the smallest instance has 100 decision bits (`2^100`
assignments).

Each instance was run with the same 30 paired seeds (`0..29`) and requested
budget of 1,024 QUBO energy evaluations. dSB used 8 agents × 128 steps = 1,024
updates each run. SA used 2 restarts; its sweep count is bounded by variable
count, so actual evaluations were 782–1,002 per run. The reported runtimes are
host-dependent and are not a solver-superiority claim.

| Public instance | Vertices / terms | Published energy | SA mean gap / matches / median time | dSB mean gap / matches / median time |
| --- | ---: | ---: | --- | --- |
| `maxcut_regular_3_100_nodes_weighted` | 100 / 150 | -68.8282 | 7.1029 / 0/30 / 0.0645 s | 4.1115 / 0/30 / 0.1746 s |
| `maxcut_regular_3_140_nodes_weighted` | 140 / 210 | -105.9703 | 14.8322 / 0/30 / 0.0931 s | 5.7517 / 0/30 / 0.2892 s |
| `maxcut_regular_3_150_nodes_weighted` | 150 / 225 | -110.9509 | 16.5545 / 0/30 / 0.0939 s | 6.5245 / 0/30 / 0.2923 s |
| `maxcut_regular_4_130_nodes_weighted` | 130 / 260 | -112.7489 | 14.7248 / 0/30 / 0.0749 s | 5.4500 / 0/30 / 0.2603 s |

All four sets of runs remained above the published energy (no below-reference
run was observed). dSB had a lower mean gap than SA on these four files, with
higher median runtime. This is descriptive of this configuration and sample
only. It does not verify the reference optimum or establish general solver
superiority.

Per-seed JSON reports:

- [`3-regular, 100 nodes`](../benchmark-results/kipu-maxcut-regular-3-100-nodes-weighted.json)
- [`3-regular, 140 nodes`](../benchmark-results/kipu-maxcut-regular-3-140-nodes-weighted.json)
- [`3-regular, 150 nodes`](../benchmark-results/kipu-maxcut-regular-3-150-nodes-weighted.json)
- [`4-regular, 130 nodes`](../benchmark-results/kipu-maxcut-regular-4-130-nodes-weighted.json)

Input SHA-256 checksums in the same order are `605651763a6ffb9f36df0f167eba8492e54ab4c6127f925be83a0bc83230cd1f`, `9fa338a06176cbaeaeb0e264220a3e722968ce8cdee086956e29a1831e3b4173`, `ce94cabd9709b018003939b816c4a7c2eaa70c1c6c68c4fe4b7955e31b34138c`, and `5d4c74a5e65f499672138e147b255f922eae928d1ce3f5795f75c66470ae37ed`. The [Kipu benchmark repository](https://github.com/Kipu-Quantum-GmbH/benchmark-instances) documents these files and references. This is still one source and four instances, not a broad benchmark survey.

## Second public source: Stanford Gset G1 and G2

To check the loader and heuristic comparison on a second public source, the
original Stanford Gset `G1` and `G2` edge lists were loaded. Both headers
declare 800 vertices and 19,176 edges; all edge weights are `+1`. The published
best-known cuts are 11,624 for G1 and 11,620 for G2, giving minimization target
energies `-11,624` and `-11,620`. These are best-known targets, not proofs of
global optimality. Stanford hosts the raw [G1](https://web.stanford.edu/~yyye/yyye/Gset/G1)
and [G2](https://web.stanford.edu/~yyye/yyye/Gset/G2) instance files; an
[independent Gset benchmark report](https://openreview.net/pdf?id=vaJ4FObpXN)
also lists these cut values. The [Quicopt Gset benchmark table](https://github.com/Quicopt/Benchmarks/blob/main/docs/gset.md)
identifies them as best-known references.

The parser converts each cut term `w*(x_i + x_j - 2*x_i*x_j)` into QUBO energy
by negating it, so minimizing the QUBO maximizes cut weight. A four-node
exhaustive unit test checks this conversion for every assignment. For G1 and
G2, `EnumerativeSolver` is not used because `2^800` assignments are out of scope.

As a separate feasibility check, the run also loaded the G1 and G2 bitstrings
from Quicopt's [Gset solution collection](https://github.com/Quicopt/Benchmarks/tree/main/GSET/solutions).
The benchmark recomputes each cut directly from its Stanford edge list with
`evaluate_gset_cut`: the declared and recomputed values both equal 11,624 for
G1 and 11,620 for G2. This confirms that the bitstrings attain the stated cuts
on these inputs. These are feasible-solution checks, not proofs that no better
cuts exist. The checked entries are in the collection's
[`gset.json`](https://raw.githubusercontent.com/Quicopt/Benchmarks/main/GSET/solutions/gset.json).

Each pilot used five paired seeds (`0..4`) and a 1,024-evaluation budget per
method. SA evaluated 801 candidates per run under its current schedule; dSB
used 8 agents × 128 updates = 1,024. Results:

| Instance | Method | Best energy | Mean energy | Mean gap to target | Matches | Mean / median runtime |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| G1 | Simulated Annealing | -10,602 | -10,563.6 | 1,060.4 | 0/5 | 2.697 / 2.728 s |
| G1 | dSB | -11,343 | -11,325.8 | 298.2 | 0/5 | 11.189 / 11.094 s |
| G2 | Simulated Annealing | -10,655 | -10,564.4 | 1,055.6 | 0/5 | 2.974 / 2.910 s |
| G2 | dSB | -11,384 | -11,355.2 | 264.8 | 0/5 | 11.330 / 11.458 s |

Neither pilot reached its published target. The runs verify the separate
edge-list parser and add five-seed quality baselines; they do not show solver
superiority or optimality. Per-seed reports are
[`G1`](../benchmark-results/stanford-gset-G1.json) and
[`G2`](../benchmark-results/stanford-gset-G2.json). Stanford input SHA-256
values are G1 `73bf704d8ffc55ba42260ab4cb659e3dcb6e729be70404d2cf476ba4e46d1665`
and G2 `732d57480a0151e81253a08535da539ff579f77dbc8673d2b58f4b051f6ccdac`;
the shared Quicopt solution JSON SHA-256 is
`ddbfa2d3b8ec71c16c0163d464b74b186f9ca660f5820405fa961e9f0818fcc3`.

## Held-out parameter-sensitivity study

The parameter study uses the same generated sparse/dense Max-Cut and knapsack
families at 8, 12, and 16 decision variables. For each family/size, two fixed
instances are used for configuration selection and a third independent
instance is held out. It uses tuning seeds `0..9`, held-out seeds `100..129`,
and a requested 1,024-energy-evaluation budget. Selection minimizes mean
relative objective gap on the training instances; median runtime breaks ties.
The holdout does not affect selection.

On the held-out knapsack instance, selected FG-dSB reached the exact objective
on 23/30 runs at 8 variables, 26/30 at 12, and 5/30 at 16; mean objective gaps
were 1.867, 2.133, and 5.433, respectively. Selected simulated annealing had
0/30 exact hits at all three sizes; selected dSB had 1/30 at 8 variables and
0/30 at 12 and 16. For the Max-Cut holdouts, selected SA achieved 23–30/30
exact hits across the six family/size cells and selected dSB achieved 25–30/30.
These are exploratory outcomes from one held-out instance per cell, not
population-level estimates. The full run JSON is in
[`benchmark-results/parameter-sensitivity.json`](../benchmark-results/parameter-sensitivity.json).

## Reproduction

From the repository root in Ubuntu/WSL:

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_generalization_benchmark.py -v

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --instances-per-setting 3 --seed-count 30 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-generalization-benchmark.json

The JSON includes instance definitions, configuration, per-seed records,
aggregated metrics, and Python/platform metadata. Use a smaller smoke run while
editing:

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --families knapsack,maxcut_sparse --sizes 4,6 --instances-per-setting 2 --seed-count 2 --evaluation-budget 64

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/parameter_sensitivity.py --output /tmp/qsagi-parameter-sensitivity.json

Download and run a public instance comparison (repeat with each filename and
reference energy in the table above; each run uses 30 paired seeds):

    curl -fL https://raw.githubusercontent.com/Kipu-Quantum-GmbH/benchmark-instances/main/maxcut/maxcut_regular_3_100_nodes_weighted.json -o /tmp/qsagi-kipu-maxcut-100.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-maxcut-json /tmp/qsagi-kipu-maxcut-100.json --public-reference-energy -68.8282 --seed-count 30 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-kipu-maxcut-results.json

    curl -fL https://raw.githubusercontent.com/Kipu-Quantum-GmbH/benchmark-instances/main/maxcut/maxcut_regular_3_140_nodes_weighted.json -o /tmp/qsagi-kipu-maxcut-140.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-maxcut-json /tmp/qsagi-kipu-maxcut-140.json --public-reference-energy -105.9703 --seed-count 30 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-kipu-maxcut-140-results.json

    curl -fL https://raw.githubusercontent.com/Kipu-Quantum-GmbH/benchmark-instances/main/maxcut/maxcut_regular_3_150_nodes_weighted.json -o /tmp/qsagi-kipu-maxcut-150.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-maxcut-json /tmp/qsagi-kipu-maxcut-150.json --public-reference-energy -110.9509 --seed-count 30 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-kipu-maxcut-150-results.json

    curl -fL https://raw.githubusercontent.com/Kipu-Quantum-GmbH/benchmark-instances/main/maxcut/maxcut_regular_4_130_nodes_weighted.json -o /tmp/qsagi-kipu-maxcut-130-r4.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-maxcut-json /tmp/qsagi-kipu-maxcut-130-r4.json --public-reference-energy -112.7489 --seed-count 30 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-kipu-maxcut-130-r4-results.json

Download and run the separate Stanford Gset pilots:

    curl -fL https://web.stanford.edu/~yyye/yyye/Gset/G1 -o /tmp/qsagi-gset-G1.txt
    curl -fL https://web.stanford.edu/~yyye/yyye/Gset/G2 -o /tmp/qsagi-gset-G2.txt

    curl -fL https://raw.githubusercontent.com/Quicopt/Benchmarks/main/GSET/solutions/gset.json -o /tmp/qsagi-quicopt-gset-solutions.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-gset-file /tmp/qsagi-gset-G1.txt --gset-best-known-cut 11624 --gset-certificate-json /tmp/qsagi-quicopt-gset-solutions.json --gset-certificate-key G1 --seed-count 5 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-gset-G1-results.json

    PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 examples/generalization_benchmark.py --skip-generated --public-gset-file /tmp/qsagi-gset-G2.txt --gset-best-known-cut 11620 --gset-certificate-json /tmp/qsagi-quicopt-gset-solutions.json --gset-certificate-key G2 --seed-count 5 --seed-start 0 --evaluation-budget 1024 --output /tmp/qsagi-gset-G2-results.json

## Limits and next validation

The exact reference cost grows exponentially; generated sizes are capped at 20
decision variables to avoid accidental unbounded exhaustive runs. The public
set now includes four Kipu instances and Stanford Gset G1/G2. The Gset
certificate checks verify attainable best-known cuts, not global optimality;
there is still no independent solver cross-check or optimality proof for these
public cases. Each Gset pilot uses five seeds and the sensitivity study has one
held-out instance per family/size. Further validation needs broader datasets
under a declared compute budget.
