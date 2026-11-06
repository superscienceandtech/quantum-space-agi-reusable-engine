"""Deterministic exhaustive solver for small finite-domain problems."""

from __future__ import annotations

from itertools import product
from typing import Protocol

from .models import OptimizationProblem, OptimizationResult, OptimizationStatus, ObjectiveSense


class Solver(Protocol):
    name: str

    def solve(self, problem: OptimizationProblem) -> OptimizationResult: ...


class EnumerativeSolver:
    """Evaluate every finite assignment; useful for small transparent baselines.

    Runtime grows exponentially with the number of variables. This solver is
    not intended as a scalable optimizer.
    """

    name = "enumerative"

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        names = tuple(sorted(problem.variables))
        domains = tuple(problem.variables[name] for name in names)
        best_solution: dict[str, float] | None = None
        best_value: float | None = None
        best_checks = ()
        evaluated = 0
        for values in product(*domains):
            candidate = problem.validate_solution(dict(zip(names, values)))
            evaluated += 1
            checks = tuple(constraint.check(candidate) for constraint in problem.constraints)
            if not all(check.feasible for check in checks):
                continue
            objective_value = problem.objective.evaluate(candidate)
            if best_value is None or self._is_better(
                objective_value, best_value, problem.objective.sense, problem.comparison_tolerance
            ):
                best_solution, best_value, best_checks = candidate, objective_value, checks
        if best_solution is None:
            return OptimizationResult(OptimizationStatus.INFEASIBLE, None, None, (), evaluated, self.name)
        return OptimizationResult(OptimizationStatus.OPTIMAL, best_solution, best_value,
                                  best_checks, evaluated, self.name)

    @staticmethod
    def _is_better(candidate: float, incumbent: float, sense: ObjectiveSense, tolerance: float) -> bool:
        if sense is ObjectiveSense.MINIMIZE:
            return candidate < incumbent - tolerance
        return candidate > incumbent + tolerance
