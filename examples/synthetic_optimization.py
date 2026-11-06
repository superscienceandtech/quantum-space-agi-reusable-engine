"""Small, challenge-independent finite optimization example."""

from quantum_space_agi.optimization import (
    ConstraintRelation,
    EnumerativeSolver,
    FunctionalConstraint,
    FunctionalObjective,
    ObjectiveSense,
    OptimizationProblem,
    OptimizationStatus,
    benchmark_solver,
)


def build_problem() -> OptimizationProblem:
    # Generic project options; no mission or NASA-specific data is encoded.
    costs = {"alpha": 4, "beta": 3, "gamma": 5, "delta": 2}
    weights = {"alpha": 3, "beta": 2, "gamma": 4, "delta": 1}
    values = {"alpha": 8, "beta": 6, "gamma": 10, "delta": 3}
    objective = FunctionalObjective(
        "maximize_total_value",
        ObjectiveSense.MAXIMIZE,
        lambda x: sum(values[key] * x[key] for key in costs),
    )
    constraints = (
        FunctionalConstraint(
            "budget", lambda x: sum(costs[key] * x[key] for key in costs),
            ConstraintRelation.LE, 7,
        ),
        FunctionalConstraint(
            "capacity", lambda x: sum(weights[key] * x[key] for key in weights),
            ConstraintRelation.LE, 5,
        ),
    )
    return OptimizationProblem(objective, {key: (0, 1) for key in costs}, constraints)


if __name__ == "__main__":
    problem = build_problem()
    report = benchmark_solver(EnumerativeSolver(), problem, repetitions=3)
    result = report.results[0]
    print(f"status: {result.status.value}")
    print(f"solution: {dict(result.solution or {})}")
    print(f"objective: {result.objective_value}")
    print(f"candidates evaluated: {result.evaluated_candidates}")
    print(f"mean runtime (seconds): {report.mean_seconds:.6f}")
    if result.status is not OptimizationStatus.OPTIMAL:
        raise SystemExit("synthetic example did not produce a feasible optimum")
