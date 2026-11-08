"""Small train/holdout parameter-sensitivity study for QUBO heuristics.

Two deterministic generated instances are used to choose among fixed parameter
candidates. A third independent instance is held out for evaluation. The split
prevents selecting and reporting parameters on the same instances.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from quantum_space_agi.optimization import EnumerativeSolver, OptimizationStatus
try:
    from examples.generalization_benchmark import (
        DEFAULT_EVALUATION_BUDGET,
        DEFAULT_FAMILIES,
        DEFAULT_SIZES,
        _quality_record,
        _summarize,
        build_instances,
    )
    from examples.qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )
except ImportError:
    from generalization_benchmark import (
        DEFAULT_EVALUATION_BUDGET,
        DEFAULT_FAMILIES,
        DEFAULT_SIZES,
        _quality_record,
        _summarize,
        build_instances,
    )
    from qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )


SA_CONFIGS = {
    "cooler_start": {"initial_temperature": 5.0, "final_temperature": 0.05},
    "baseline": {"initial_temperature": 10.0, "final_temperature": 0.05},
    "hotter_start": {"initial_temperature": 20.0, "final_temperature": 0.05},
}
DSB_CONFIGS = {
    "pump_1_5": {"pump_end": 1.5},
    "baseline": {"pump_end": 2.0},
    "pump_2_5": {"pump_end": 2.5},
}
FG_CONFIGS = {
    "one_flip": {"max_flip_size": 1},
    "baseline": {"max_flip_size": 2},
}


def _evaluate_configuration(instance, method, config, seeds, budget):
    exact = EnumerativeSolver().solve(instance.problem)
    if exact.status is not OptimizationStatus.OPTIMAL or exact.objective_value is None:
        raise RuntimeError(f"{instance.name}: exact feasible reference required")

    variable_count = len(instance.qubo.variable_order)
    dsb_agents = min(8, max(1, budget // 2))
    dsb_steps = max(1, budget // dsb_agents)
    sa_restarts = min(4, max(1, budget // (2 * variable_count)))
    sa_sweeps = max(1, (budget - sa_restarts) // (sa_restarts * variable_count))
    records = []

    for seed in seeds:
        started = perf_counter()
        if method == "simulated_annealing":
            result = simulated_annealing_qubo(
                instance.qubo,
                seed=seed,
                sweeps=sa_sweeps,
                restarts=sa_restarts,
                initial_temperature=config["initial_temperature"],
                final_temperature=config["final_temperature"],
            )
            state, energy = result.state, result.energy
            evaluations, repair_evaluations = result.proposals_evaluated + sa_restarts, 0
        elif method == "discrete_sb":
            result = discrete_simulated_bifurcation_qubo(
                instance.qubo,
                seed=seed,
                agents=dsb_agents,
                steps=dsb_steps,
                pump_end=config["pump_end"],
            )
            state, energy = result.state, result.energy
            evaluations, repair_evaluations = result.updates_evaluated, 0
        elif method == "fg_dsb":
            result = feasibility_guided_dsb(
                instance.qubo,
                instance.problem,
                instance.linear_constraints,
                seed=seed,
                agents=dsb_agents,
                steps=dsb_steps,
                max_flip_size=config["max_flip_size"],
            )
            state, energy = result.state, result.energy
            evaluations = dsb_agents * dsb_steps
            repair_evaluations = result.repair_candidates_evaluated
        else:
            raise ValueError(f"unsupported method: {method}")
        runtime = perf_counter() - started
        records.append(
            _quality_record(
                instance,
                state,
                energy,
                optimal_value=exact.objective_value,
                seed=seed,
                runtime_seconds=runtime,
                energy_evaluations=evaluations,
                repair_evaluations=repair_evaluations,
            )
        )

    summary = _summarize(records)
    relative_gaps = [
        float(record["relative_optimality_gap"])
        for record in records
        if record["relative_optimality_gap"] is not None
    ]
    summary["mean_relative_optimality_gap"] = (
        mean(relative_gaps) if relative_gaps else None
    )
    return {"summary": summary, "runs": records}


def _select_configuration(training_results):
    def score(item):
        summary = item[1]["summary"]
        gap = summary["mean_relative_optimality_gap"]
        return (
            float("inf") if gap is None else float(gap),
            float(summary["median_runtime_seconds"]),
        )
    return min(training_results.items(), key=score)


def _study_cell(family, size, *, tuning_seeds, holdout_seeds, budget):
    instances = build_instances((family,), (size,), instances_per_setting=3)
    training_instances = instances[:2]
    holdout_instance = instances[2]

    method_configs = {
        "simulated_annealing": SA_CONFIGS,
        "discrete_sb": DSB_CONFIGS,
    }
    if family == "knapsack":
        method_configs["fg_dsb"] = FG_CONFIGS

    method_results = {}
    for method, configs in method_configs.items():
        training_results = {}
        for config_name, config in configs.items():
            runs = []
            for instance in training_instances:
                result = _evaluate_configuration(
                    instance, method, config, tuning_seeds, budget
                )
                runs.extend(result["runs"])
            summary = _summarize(runs)
            gaps = [
                float(record["relative_optimality_gap"])
                for record in runs
                if record["relative_optimality_gap"] is not None
            ]
            summary["mean_relative_optimality_gap"] = mean(gaps) if gaps else None
            training_results[config_name] = {"summary": summary}

        selected_name, _ = _select_configuration(training_results)
        baseline_name = "baseline"
        holdout_results = {}
        for config_name in sorted({selected_name, baseline_name}):
            holdout_results[config_name] = _evaluate_configuration(
                holdout_instance,
                method,
                configs[config_name],
                holdout_seeds,
                budget,
            )

        method_results[method] = {
            "training_instance_seeds": [
                instance.instance_seed for instance in training_instances
            ],
            "holdout_instance_seed": holdout_instance.instance_seed,
            "training_configuration_summaries": training_results,
            "selected_configuration": selected_name,
            "baseline_configuration": baseline_name,
            "holdout_baseline": holdout_results[baseline_name]["summary"],
            "holdout_selected": holdout_results[selected_name]["summary"],
        }

    return {
        "family": family,
        "decision_variable_count": size,
        "training_instances": len(training_instances),
        "holdout_instances": 1,
        "methods": method_results,
    }


def run_study(
    *,
    families=DEFAULT_FAMILIES,
    sizes=DEFAULT_SIZES,
    tuning_seed_count=10,
    holdout_seed_count=30,
    budget=DEFAULT_EVALUATION_BUDGET,
):
    if tuning_seed_count < 1 or holdout_seed_count < 1:
        raise ValueError("tuning and holdout seed counts must be positive")
    tuning_seeds = tuple(range(tuning_seed_count))
    holdout_seeds = tuple(range(100, 100 + holdout_seed_count))
    return {
        "study": "held-out parameter sensitivity",
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "protocol": {
            "families": families,
            "sizes": sizes,
            "independent_instances_per_setting": 3,
            "training_instances_per_setting": 2,
            "holdout_instances_per_setting": 1,
            "tuning_seeds": tuning_seeds,
            "holdout_seeds": holdout_seeds,
            "requested_energy_evaluation_budget": budget,
            "selection_rule": "lowest mean relative objective gap on training instances; median runtime breaks ties",
            "holdout_is_not_used_for_selection": True,
        },
        "results": [
            _study_cell(
                family,
                size,
                tuning_seeds=tuning_seeds,
                holdout_seeds=holdout_seeds,
                budget=budget,
            )
            for family in families
            for size in sizes
        ],
        "limitations": [
            "Only three synthetic instances per family/size setting.",
            "Parameter candidates are a small predeclared grid, not an exhaustive search.",
            "A single held-out instance per family/size gives exploratory evidence only.",
            "This study does not establish general superiority or quantum advantage.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--families",
        default=",".join(DEFAULT_FAMILIES),
        help="comma-separated: maxcut_sparse,maxcut_dense,knapsack",
    )
    parser.add_argument("--sizes", default="8,12,16")
    parser.add_argument("--tuning-seeds", type=int, default=10)
    parser.add_argument("--holdout-seeds", type=int, default=30)
    parser.add_argument("--evaluation-budget", type=int, default=DEFAULT_EVALUATION_BUDGET)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    families = tuple(part.strip() for part in args.families.split(",") if part.strip())
    try:
        sizes = tuple(int(part.strip()) for part in args.sizes.split(",") if part.strip())
    except ValueError as error:
        parser.error(f"invalid sizes: {error}")
    report = run_study(
        families=families,
        sizes=sizes,
        tuning_seed_count=args.tuning_seeds,
        holdout_seed_count=args.holdout_seeds,
        budget=args.evaluation_budget,
    )
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output is None:
        print(serialized)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Wrote parameter-sensitivity report to {args.output}")


if __name__ == "__main__":
    main()