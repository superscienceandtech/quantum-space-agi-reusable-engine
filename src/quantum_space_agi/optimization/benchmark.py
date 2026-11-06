"""Small repeatable timing harness for solver comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from time import perf_counter

from .models import OptimizationProblem, OptimizationResult
from .solver import Solver


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    solver_name: str
    repetitions: int
    elapsed_seconds: tuple[float, ...]
    mean_seconds: float
    min_seconds: float
    results: tuple[OptimizationResult, ...]


def benchmark_solver(solver: Solver, problem: OptimizationProblem, repetitions: int = 3) -> BenchmarkReport:
    """Report repeated wall-clock timings; results remain machine-dependent."""
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    durations: list[float] = []
    results: list[OptimizationResult] = []
    for _ in range(repetitions):
        start = perf_counter()
        results.append(solver.solve(problem))
        durations.append(perf_counter() - start)
    return BenchmarkReport(solver.name, repetitions, tuple(durations), mean(durations),
                          min(durations), tuple(results))
