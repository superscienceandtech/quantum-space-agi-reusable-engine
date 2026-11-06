"""Generic optimization interfaces and a deterministic classical baseline."""

from .benchmark import BenchmarkReport, benchmark_solver
from .interfaces import Constraint, ConstraintCheck, FunctionalConstraint, FunctionalObjective, Objective
from .models import ConstraintRelation, OptimizationProblem, OptimizationResult, OptimizationStatus, ObjectiveSense
from .solver import EnumerativeSolver, Solver

__all__ = [
    "BenchmarkReport", "Constraint", "ConstraintCheck", "ConstraintRelation",
    "EnumerativeSolver", "FunctionalConstraint", "FunctionalObjective", "Objective",
    "ObjectiveSense", "OptimizationProblem", "OptimizationResult", "OptimizationStatus",
    "Solver", "benchmark_solver",
]
