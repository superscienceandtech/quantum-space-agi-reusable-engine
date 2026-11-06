"""Deterministic, challenge-independent examples for the classical baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass

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
    benchmark_solver,
)

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
    infeasible_diagnostic_candidate: dict[str, float] | None = None


def _make_case(
    name: str,
    description: str,
    budget_limit: float,
    capacity_limit: float,
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
    problem = OptimizationProblem(
        objective=objective,
        variables={name: (0, 1) for name in VALUES},
        constraints=tuple(constraints),
    )
    return ExampleCase(
        name,
        description,
        problem,
        objective_counter,
        tuple(constraint_inputs),
        diagnostic_candidate,
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


def _checks_for_diagnostic(
    problem: OptimizationProblem, candidate: dict[str, float]
) -> tuple[ConstraintCheck, ...]:
    validated = problem.validate_solution(candidate)
    return tuple(constraint.check(validated) for constraint in problem.constraints)


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
        "input": {
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
    reports = [run_case(case) for case in build_cases()]
    print(json.dumps(reports, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
