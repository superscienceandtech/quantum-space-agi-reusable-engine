"""Compare classical SA, discrete SB, and feasibility-guided dSB on QUBOs."""

from __future__ import annotations

import argparse
import json
from statistics import mean, median
from time import perf_counter

try:
    from examples.synthetic_optimization import _minimum_energy_state, build_cases
except ImportError:
    from synthetic_optimization import _minimum_energy_state, build_cases
from quantum_space_agi.optimization import EnumerativeSolver, OptimizationStatus
from quantum_space_agi.optimization.qubo import build_qubo
try:
    from examples.qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )
except ImportError:
    from qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )


def _measure_state(case, model, bits):
    decisions = dict(model.decode(bits))
    validated = case.problem.validate_solution(decisions)
    checks = tuple(constraint.check(validated) for constraint in case.problem.constraints)
    feasible = all(check.feasible for check in checks)
    objective = case.problem.objective.evaluate(validated) if feasible else None
    return feasible, objective


def _summary(records):
    feasible = sum(bool(record["feasible"]) for record in records)
    exact_energy = sum(bool(record["matches_exact_energy"]) for record in records)
    runtimes = [record["runtime_seconds"] for record in records]
    objective_optima = [record["matches_original_optimum"] for record in records]
    known_optima = [value for value in objective_optima if value is not None]
    return {
        "runs": len(records),
        "feasible_runs": feasible,
        "feasibility_rate": feasible / len(records),
        "exact_qubo_energy_runs": exact_energy,
        "exact_qubo_energy_rate": exact_energy / len(records),
        "original_objective_optimum_runs": sum(bool(value) for value in known_optima),
        "original_objective_optimum_rate": (
            sum(bool(value) for value in known_optima) / len(known_optima)
            if known_optima else None
        ),
        "mean_runtime_seconds": mean(runtimes),
        "median_runtime_seconds": median(runtimes),
        "minimum_runtime_seconds": min(runtimes),
    }


def run_case(case, seeds=tuple(range(20))):
    model = build_qubo(
        tuple(sorted(case.problem.variables)),
        {"alpha": 6, "beta": 4, "gamma": 3},
        case.problem.objective.sense,
        case.qubo_constraints,
    )
    exact_state, exact_energy, exact_count = _minimum_energy_state(model)
    exact_original = EnumerativeSolver().solve(case.problem)
    exact_feasible, exact_objective = _measure_state(case, model, exact_state)
    records = {"simulated_annealing": [], "discrete_sb": [], "fg_dsb": [], "exact_qubo": []}
    for seed in seeds:
        started = perf_counter()
        sa = simulated_annealing_qubo(model, seed=seed)
        sa_time = perf_counter() - started
        sa_feasible, sa_objective = _measure_state(case, model, sa.state)
        records["simulated_annealing"].append({
            "seed": seed, "energy": sa.energy,
            "matches_exact_energy": abs(sa.energy - exact_energy) <= 1e-12,
            "feasible": sa_feasible,
            "matches_original_optimum": (
                abs(sa_objective - exact_original.objective_value) <= 1e-12
                if sa_feasible and exact_original.status is OptimizationStatus.OPTIMAL else None
            ),
            "updates": sa.proposals_evaluated, "runtime_seconds": sa_time,
        })

        started = perf_counter()
        dsb = discrete_simulated_bifurcation_qubo(model, seed=seed, agents=8, steps=96)
        dsb_time = perf_counter() - started
        dsb_feasible, dsb_objective = _measure_state(case, model, dsb.state)
        records["discrete_sb"].append({
            "seed": seed, "energy": dsb.energy,
            "matches_exact_energy": abs(dsb.energy - exact_energy) <= 1e-12,
            "feasible": dsb_feasible,
            "matches_original_optimum": (
                abs(dsb_objective - exact_original.objective_value) <= 1e-12
                if dsb_feasible and exact_original.status is OptimizationStatus.OPTIMAL else None
            ),
            "updates": dsb.updates_evaluated, "runtime_seconds": dsb_time,
        })

        started = perf_counter()
        fg = feasibility_guided_dsb(
            model, case.problem, case.qubo_constraints,
            seed=seed, agents=8, steps=96, max_flip_size=2,
        )
        fg_time = perf_counter() - started
        records["fg_dsb"].append({
            "seed": seed, "energy": fg.energy,
            "matches_exact_energy": abs(fg.energy - exact_energy) <= 1e-12,
            "feasible": fg.feasible,
            "matches_original_optimum": (
                abs(fg.objective_value - exact_original.objective_value) <= 1e-12
                if fg.feasible and exact_original.status is OptimizationStatus.OPTIMAL else None
            ),
            "repair_moves": fg.repair_moves,
            "repair_candidates_evaluated": fg.repair_candidates_evaluated,
            "runtime_seconds": fg_time,
        })

        started = perf_counter()
        repeated_state, repeated_energy, repeated_count = _minimum_energy_state(model)
        exact_time = perf_counter() - started
        if repeated_energy != exact_energy or repeated_count != exact_count:
            raise RuntimeError("exact QUBO reference changed between repetitions")
        exact_feasible, exact_objective = _measure_state(case, model, repeated_state)
        records["exact_qubo"].append({
            "seed": seed, "energy": repeated_energy,
            "matches_exact_energy": repeated_energy == exact_energy,
            "feasible": exact_feasible,
            "matches_original_optimum": (
                abs(exact_objective - exact_original.objective_value) <= 1e-12
                if exact_feasible and exact_original.status is OptimizationStatus.OPTIMAL else None
            ),
            "updates": repeated_count, "runtime_seconds": exact_time,
        })

    return {
        "case": case.name,
        "configuration": {
            "seeds": seeds,
            "d_sb_agents": 8,
            "d_sb_steps": 96,
            "fg_dsb_repair_neighborhood": "all one- and two-decision-bit flips",
            "sa_restarts": 4,
            "sa_sweeps_per_restart": 64,
            "exact_qubo_states": exact_count,
        },
        "original_exact_status": exact_original.status.value,
        "original_exact_objective": exact_original.objective_value,
        "exact_qubo_energy": exact_energy,
        "methods": {
            name: {"summary": _summary(items), "runs": items}
            for name, items in records.items()
        },
        "scope_note": (
            "Small synthetic pilot only. Python CPU timings are not a hardware or "
            "performance claim; FG-dSB is a project-specific research candidate, "
            "not a claim of established literature novelty."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="0,1,2")
    args = parser.parse_args()
    seeds = tuple(int(value) for value in args.seeds.split(",") if value.strip())
    if not seeds or len(set(seeds)) != len(seeds):
        raise SystemExit("--seeds must be a non-empty comma-separated list of unique integers")
    print(json.dumps({"cases": [run_case(case, seeds) for case in build_cases()]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
