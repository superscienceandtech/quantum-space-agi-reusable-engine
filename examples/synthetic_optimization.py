"""Deterministic, challenge-independent examples for the classical baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import product
from statistics import mean, median
from time import perf_counter

from quantum_space_agi.optimization import (
    Constraint,
    ConstraintCheck,
    ConstraintRelation,
    EnumerativeSolver,
    FunctionalConstraint,
    FunctionalObjective,
    ObjectiveSense,
    OptimizationProblem,
    OptimizationResult,
    OptimizationStatus,
    benchmark_solver,
)
from quantum_space_agi.optimization.qubo import LinearConstraintSpec, QUBOModel, build_qubo
try:
    from examples.qubo_heuristics import simulated_annealing_qubo
except ImportError:
    from qubo_heuristics import simulated_annealing_qubo

REPETITIONS = 5
VALUES = {"alpha": 6, "beta": 4, "gamma": 3}
COSTS = {"alpha": 3, "beta": 2, "gamma": 2}
WEIGHTS = {"alpha": 2, "beta": 1, "gamma": 1}


class CountingValue:
    """Count objective calls without changing the public solver contract."""

    def __init__(self, coefficients: dict[str, float]) -> None:
        self.coefficients = coefficients
        self.calls = 0

    def __call__(self, solution: dict[str, float]) -> float:
        self.calls += 1
        return sum(self.coefficients[name] * solution[name] for name in self.coefficients)


@dataclass(frozen=True)
class ExampleCase:
    name: str
    description: str
    problem: OptimizationProblem
    objective_counter: CountingValue
    constraint_inputs: tuple[dict[str, object], ...]
    qubo_constraints: tuple[LinearConstraintSpec, ...] = ()
    infeasible_diagnostic_candidate: dict[str, float] | None = None
    input_override: dict[str, object] | None = None


def _make_case(
    name: str,
    description: str,
    budget_limit: int,
    capacity_limit: int,
    *,
    minimum_selected: int | None = None,
    diagnostic_candidate: dict[str, float] | None = None,
) -> ExampleCase:
    objective_counter = CountingValue(VALUES)
    objective = FunctionalObjective(
        "maximize_total_value", ObjectiveSense.MAXIMIZE, objective_counter
    )
    constraints: list[Constraint] = [
        FunctionalConstraint(
            "budget",
            lambda x: sum(COSTS[key] * x[key] for key in COSTS),
            ConstraintRelation.LE,
            budget_limit,
        ),
        FunctionalConstraint(
            "capacity",
            lambda x: sum(WEIGHTS[key] * x[key] for key in WEIGHTS),
            ConstraintRelation.LE,
            capacity_limit,
        ),
    ]
    constraint_inputs: list[dict[str, object]] = [
        {
            "name": "budget",
            "expression": "3*alpha + 2*beta + 2*gamma",
            "relation": ConstraintRelation.LE.value,
            "bound": budget_limit,
            "tolerance": 0.0,
        },
        {
            "name": "capacity",
            "expression": "2*alpha + beta + gamma",
            "relation": ConstraintRelation.LE.value,
            "bound": capacity_limit,
            "tolerance": 0.0,
        },
    ]
    if minimum_selected is not None:
        constraints.append(
            FunctionalConstraint(
                "minimum_selected",
                lambda x: sum(x.values()),
                ConstraintRelation.GE,
                minimum_selected,
            )
        )
        constraint_inputs.append(
            {
                "name": "minimum_selected",
                "expression": "alpha + beta + gamma",
                "relation": ConstraintRelation.GE.value,
                "bound": minimum_selected,
                "tolerance": 0.0,
            }
        )
    qubo_constraints = [
        LinearConstraintSpec("budget", COSTS, ConstraintRelation.LE, budget_limit),
        LinearConstraintSpec("capacity", WEIGHTS, ConstraintRelation.LE, capacity_limit),
    ]
    if minimum_selected is not None:
        qubo_constraints.append(
            LinearConstraintSpec(
                "minimum_selected",
                {name: 1 for name in VALUES},
                ConstraintRelation.GE,
                minimum_selected,
            )
        )
    problem = OptimizationProblem(
        objective=objective,
        variables={name: (0, 1) for name in VALUES},
        constraints=tuple(constraints),
    )
    return ExampleCase(
        name=name,
        description=description,
        problem=problem,
        objective_counter=objective_counter,
        constraint_inputs=tuple(constraint_inputs),
        qubo_constraints=tuple(qubo_constraints),
        infeasible_diagnostic_candidate=diagnostic_candidate,
    )


def build_cases() -> tuple[ExampleCase, ...]:
    """Build three deterministic fixtures over identical domains/objective."""
    return (
        _make_case("feasible", "Feasible baseline at the stated resource limits.", 5, 3),
        _make_case("resource_constrained", "Tighter resource limits; a feasible plan remains.", 4, 2),
        _make_case(
            "infeasible",
            "Selecting all options is required, but exceeds the resource limits.",
            4,
            3,
            minimum_selected=3,
            diagnostic_candidate={"alpha": 1, "beta": 1, "gamma": 1},
        ),
    )


def build_scaling_cases(sizes: tuple[int, ...] = (3, 6, 9, 12)) -> tuple[ExampleCase, ...]:
    """Build feasible binary fixtures with exactly 2**size assignments each."""
    cases = []
    for size in sizes:
        if size < 1:
            raise ValueError("scaling problem sizes must be positive")
        names = tuple(f"x{index:02d}" for index in range(size))
        values = {name: float(1 + (index * 3) % 7) for index, name in enumerate(names)}
        resource_use = {name: float(1 + (index * 5) % 4) for index, name in enumerate(names)}
        capacity_limit = float(size * 1.5)
        objective_counter = CountingValue(values)
        objective = FunctionalObjective(
            "maximize_total_value", ObjectiveSense.MAXIMIZE, objective_counter
        )
        constraint = FunctionalConstraint(
            "resource_capacity",
            lambda x, weights=resource_use: sum(weights[name] * x[name] for name in weights),
            ConstraintRelation.LE,
            capacity_limit,
        )
        problem = OptimizationProblem(
            objective=objective,
            variables={name: (0, 1) for name in names},
            constraints=(constraint,),
        )
        constraint_inputs = ({
            "name": "resource_capacity",
            "expression_coefficients": resource_use,
            "relation": ConstraintRelation.LE.value,
            "bound": capacity_limit,
            "tolerance": 0.0,
        },)
        input_override = {
            "variables": {name: [0, 1] for name in names},
            "objective": {
                "name": objective.name,
                "sense": objective.sense.value,
                "coefficients": values,
            },
            "constraints": list(constraint_inputs),
        }
        cases.append(ExampleCase(
            name=f"scaling_n{size}",
            description=f"Deterministic binary scaling fixture with {size} variables.",
            problem=problem,
            objective_counter=objective_counter,
            constraint_inputs=constraint_inputs,
            input_override=input_override,
        ))
    return tuple(cases)


def _checks_for_diagnostic(
    problem: OptimizationProblem, candidate: dict[str, float]
) -> tuple[ConstraintCheck, ...]:
    validated = problem.validate_solution(candidate)
    return tuple(constraint.check(validated) for constraint in problem.constraints)


def _minimum_energy_state(model: QUBOModel) -> tuple[dict[str, int], float, int]:
    """Find a QUBO minimum by classical exhaustive bitstring enumeration."""
    best_bits: dict[str, int] | None = None
    best_energy: float | None = None
    evaluated = 0
    for bit_values in product((0, 1), repeat=len(model.variable_order)):
        bits = dict(zip(model.variable_order, bit_values))
        energy = model.energy(bits)
        evaluated += 1
        if best_energy is None or energy < best_energy:
            best_bits, best_energy = bits, energy
    assert best_bits is not None and best_energy is not None
    return best_bits, best_energy, evaluated


def run_qubo_case(case: ExampleCase) -> dict[str, object]:
    """Encode one case, classically enumerate QUBO states, and compare feasibility."""
    model = build_qubo(
        decision_variables=tuple(sorted(case.problem.variables)),
        objective_coefficients=VALUES,
        objective_sense=case.problem.objective.sense,
        constraints=case.qubo_constraints,
    )
    bits, energy, qubo_states_evaluated = _minimum_energy_state(model)
    bitstring = "".join(str(bits[name]) for name in model.variable_order)
    decoded = dict(model.decode(bitstring))
    validated = case.problem.validate_solution(decoded)
    constraint_checks = tuple(constraint.check(validated) for constraint in case.problem.constraints)
    decoded_feasible = all(check.feasible for check in constraint_checks)
    decoded_objective = case.problem.objective.evaluate(validated) if decoded_feasible else None
    exact = EnumerativeSolver().solve(case.problem)

    if exact.status is OptimizationStatus.OPTIMAL:
        if not decoded_feasible:
            raise AssertionError(f"{case.name}: QUBO minimum decoded to an infeasible assignment")
        if decoded != dict(exact.solution or {}):
            raise AssertionError(f"{case.name}: QUBO and exact solver chose different assignments")
        if decoded_objective != exact.objective_value:
            raise AssertionError(f"{case.name}: QUBO and exact objective values differ")
        solution_match: bool | None = True
    else:
        if decoded_feasible:
            raise AssertionError(f"{case.name}: QUBO decoded as feasible while exact solver reports infeasible")
        solution_match = None

    return {
        "case": case.name,
        "method": "classical exhaustive enumeration of QUBO bitstrings; no quantum sampling",
        "qubo": {
            "variable_order": model.variable_order,
            "bitstring": bitstring,
            "minimum_energy": energy,
            "penalty_coefficient": model.penalty_coefficient,
            "slack_values": dict(model.decode_slacks(bitstring)),
            "bitstrings_evaluated": qubo_states_evaluated,
        },
        "decoded": {
            "decision_variables": decoded,
            "feasible": decoded_feasible,
            "objective_value": decoded_objective,
            "constraint_results": [
                {
                    "name": check.name,
                    "value": check.value,
                    "relation": check.relation.value,
                    "bound": check.bound,
                    "feasible": check.feasible,
                    "violation": check.violation,
                }
                for check in constraint_checks
            ],
        },
        "exact_enumerative_baseline": {
            "status": exact.status.value,
            "solution": dict(exact.solution) if exact.solution is not None else None,
            "objective_value": exact.objective_value,
            "candidates_evaluated": exact.evaluated_candidates,
        },
        "comparison": {
            "feasibility_agrees": (exact.status is OptimizationStatus.OPTIMAL) == decoded_feasible,
            "same_feasible_solution": solution_match,
            "note": (
                "No exact feasible solution exists; decoded QUBO state remains infeasible."
                if exact.status is OptimizationStatus.INFEASIBLE
                else "Decoded feasible optimum matches exact enumeration."
            ),
        },
    }


def run_annealing_case(case: ExampleCase, seeds: tuple[int, ...] = tuple(range(20))) -> dict[str, object]:
    """Compare seeded classical QUBO annealing runs with exact references."""
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be a non-empty tuple of unique integers")
    model = build_qubo(
        decision_variables=tuple(sorted(case.problem.variables)),
        objective_coefficients=VALUES,
        objective_sense=case.problem.objective.sense,
        constraints=case.qubo_constraints,
    )
    exact_state, exact_energy, exact_states = _minimum_energy_state(model)
    exact_bitstring = "".join(str(exact_state[name]) for name in model.variable_order)
    exact_problem_result = EnumerativeSolver().solve(case.problem)
    records: list[dict[str, object]] = []
    results = []
    runtimes: list[float] = []
    exact_runtimes: list[float] = []

    for seed in seeds:
        exact_started = perf_counter()
        repeated_state, repeated_energy, repeated_count = _minimum_energy_state(model)
        exact_runtimes.append(perf_counter() - exact_started)
        if repeated_energy != exact_energy or repeated_count != exact_states:
            raise RuntimeError("exact QUBO reference changed across repetitions")
        started = perf_counter()
        result = simulated_annealing_qubo(model, seed=seed)
        runtimes.append(perf_counter() - started)
        results.append(result)
        decoded = dict(model.decode(result.state))
        validated = case.problem.validate_solution(decoded)
        checks = tuple(constraint.check(validated) for constraint in case.problem.constraints)
        feasible = all(check.feasible for check in checks)
        records.append({
            "seed": seed,
            "energy": result.energy,
            "matches_exact_qubo_energy": abs(result.energy - exact_energy) <= 1e-12,
            "feasible": feasible,
            "proposals_evaluated": result.proposals_evaluated,
            "accepted_moves": result.accepted_moves,
            "runtime_seconds": runtimes[-1],
            "exact_enumeration_runtime_seconds": exact_runtimes[-1],
        })

    best_index = min(range(len(records)), key=lambda index: records[index]["energy"])
    best_run = results[best_index]
    best_decision = dict(model.decode(best_run.state))
    best_validated = case.problem.validate_solution(best_decision)
    best_checks = tuple(constraint.check(best_validated) for constraint in case.problem.constraints)
    best_feasible = all(check.feasible for check in best_checks)
    best_objective = case.problem.objective.evaluate(best_validated) if best_feasible else None
    optimal_runs = sum(bool(record["matches_exact_qubo_energy"]) for record in records)
    feasible_runs = sum(bool(record["feasible"]) for record in records)

    return {
        "case": case.name,
        "method": "classical simulated annealing with single-bit Metropolis updates",
        "configuration": {
            "seeds": seeds,
            "restarts_per_seed": 4,
            "sweeps_per_restart": 64,
            "initial_temperature": 10.0,
            "final_temperature": 0.05,
            "proposals_per_run": 4 * 64 * len(model.variable_order),
        },
        "reference": {
            "exact_qubo_energy": exact_energy,
            "exact_qubo_bitstring": exact_bitstring,
            "qubo_bitstrings_evaluated": exact_states,
            "original_solver_status": exact_problem_result.status.value,
            "original_objective_value": exact_problem_result.objective_value,
        },
        "summary": {
            "optimal_energy_runs": optimal_runs,
            "run_count": len(records),
            "optimal_energy_rate": optimal_runs / len(records),
            "feasible_runs": feasible_runs,
            "feasibility_rate": feasible_runs / len(records),
            "mean_runtime_seconds": mean(runtimes),
            "median_runtime_seconds": median(runtimes),
            "minimum_runtime_seconds": min(runtimes),
            "exact_enumeration_mean_seconds": mean(exact_runtimes),
            "exact_enumeration_median_seconds": median(exact_runtimes),
            "exact_enumeration_minimum_seconds": min(exact_runtimes),
        },
        "best_visited_state": {
            "decision_variables": best_decision,
            "energy": best_run.energy,
            "feasible": best_feasible,
            "objective_value": best_objective,
            "constraint_violations": {check.name: check.violation for check in best_checks},
        },
        "runs": records,
        "interpretation": (
            "Small synthetic heuristic study only; no optimality, hardware, "
            "quantum-inspired, or quantum-advantage claim."
        ),
    }


def run_case(case: ExampleCase, repetitions: int = REPETITIONS) -> dict[str, object]:
    """Solve, repeat the benchmark, and serialize deterministic result details."""
    solver = EnumerativeSolver()
    benchmark = benchmark_solver(solver, case.problem, repetitions=repetitions)
    results: tuple[OptimizationResult, ...] = benchmark.results
    first = results[0]
    signature = (first.status, dict(first.solution or {}), first.objective_value,
                 first.constraint_checks, first.evaluated_candidates)
    if any(
        (r.status, dict(r.solution or {}), r.objective_value, r.constraint_checks,
         r.evaluated_candidates) != signature
        for r in results[1:]
    ):
        raise RuntimeError(f"{case.name}: repeated solver outputs were not identical")
    if case.objective_counter.calls % repetitions:
        raise RuntimeError(f"{case.name}: objective-call count varied across repetitions")

    if first.solution is not None:
        diagnostic = dict(first.solution)
        checks = first.constraint_checks
        diagnostic_source = "solver_solution"
    else:
        diagnostic = case.infeasible_diagnostic_candidate or {}
        checks = _checks_for_diagnostic(case.problem, diagnostic)
        diagnostic_source = "explicit_diagnostic_witness"

    return {
        "case": case.name,
        "description": case.description,
        "input": case.input_override or {
            "variables": {name: list(values) for name, values in case.problem.variables.items()},
            "objective": {
                "name": case.problem.objective.name,
                "sense": case.problem.objective.sense.value,
                "coefficients": VALUES,
            },
            "constraints": list(case.constraint_inputs),
        },
        "solver": {
            "name": solver.name,
            "configuration": {
                "comparison_tolerance": case.problem.comparison_tolerance,
                "enumeration_order": "variable names lexical; domain values in declared order",
            },
        },
        "benchmark": {
            "repetitions": repetitions,
            "timing_method": "time.perf_counter around solver.solve(problem)",
            "timing_samples_seconds": benchmark.elapsed_seconds,
            "mean_seconds": benchmark.mean_seconds,
            "median_seconds": median(benchmark.elapsed_seconds),
            "min_seconds": benchmark.min_seconds,
            "seed": None,
            "seed_policy": "not applicable; solver is deterministic and uses no randomness",
            "output_format": "JSON, sorted keys",
        },
        "result": {
            "status": first.status.value,
            "solution": dict(first.solution) if first.solution is not None else None,
            "objective_value": first.objective_value,
            "constraint_diagnostic_source": diagnostic_source,
            "diagnostic_candidate": diagnostic,
            "constraint_results": [
                {
                    "name": check.name,
                    "value": check.value,
                    "relation": check.relation.value,
                    "bound": check.bound,
                    "tolerance": check.tolerance,
                    "feasible": check.feasible,
                    "violation": check.violation,
                }
                for check in checks
            ],
            "candidates_evaluated_per_solve": first.evaluated_candidates,
            "candidates_evaluated_across_repetitions": sum(
                result.evaluated_candidates for result in results
            ),
            "objective_evaluations_per_solve": case.objective_counter.calls // repetitions,
        },
        "timing_note": "Tiny exhaustive examples are for correctness and reproducibility, not performance claims.",
    }


def main() -> None:
    output = {
        "scenarios": [run_case(case) for case in build_cases()],
        "qubo_experiments": [run_qubo_case(case) for case in build_cases()],
        "qubo_annealing_evaluation": [run_annealing_case(case) for case in build_cases()],
        "scaling": [run_case(case) for case in build_scaling_cases()],
        "scaling_note": (
            "Candidate counts grow exponentially with binary variable count; "
            "timings are for reproducibility, not performance claims."
        ),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
