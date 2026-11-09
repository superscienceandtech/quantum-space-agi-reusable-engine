"""Validated value objects for finite-domain optimization problems."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import Constraint, ConstraintCheck, Objective


class ObjectiveSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ConstraintRelation(str, Enum):
    LE = "<="
    GE = ">="
    EQ = "=="


class OptimizationStatus(str, Enum):
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"


@dataclass(frozen=True, slots=True)
class OptimizationProblem:
    objective: Objective
    variables: Mapping[str, tuple[float, ...]]
    constraints: tuple[Constraint, ...] = ()
    comparison_tolerance: float = 1e-12

    def __post_init__(self) -> None:
        if not isfinite(self.comparison_tolerance) or self.comparison_tolerance < 0:
            raise ValueError("comparison_tolerance must be finite and non-negative")
        copied: dict[str, tuple[float, ...]] = {}
        for name, values in self.variables.items():
            if not name.strip():
                raise ValueError("variable names must not be empty")
            domain = tuple(float(value) for value in values)
            if not domain:
                raise ValueError(f"domain for variable {name!r} must not be empty")
            if any(not isfinite(value) for value in domain):
                raise ValueError(
                    f"domain for variable {name!r} contains a non-finite value"
                )
            if len(set(domain)) != len(domain):
                raise ValueError(
                    f"domain for variable {name!r} contains duplicate values"
                )
            copied[name] = domain
        if not copied:
            raise ValueError(
                "an optimization problem must define at least one variable"
            )
        object.__setattr__(self, "variables", MappingProxyType(copied))
        object.__setattr__(self, "constraints", tuple(self.constraints))

    def validate_solution(self, solution: Mapping[str, float]) -> Mapping[str, float]:
        """Check that a candidate supplies exactly one allowed value per variable."""
        expected = set(self.variables)
        actual = set(solution)
        missing = expected - actual
        extra = actual - expected
        if missing or extra:
            details = []
            if missing:
                details.append(f"missing variables: {sorted(missing)}")
            if extra:
                details.append(f"unknown variables: {sorted(extra)}")
            raise ValueError("; ".join(details))
        normalized = {name: float(solution[name]) for name in self.variables}
        for name, value in normalized.items():
            if not isfinite(value):
                raise ValueError(f"value for variable {name!r} must be finite")
            if value not in self.variables[name]:
                raise ValueError(
                    f"value {value!r} is outside the domain for variable {name!r}"
                )
        return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    status: OptimizationStatus
    solution: Mapping[str, float] | None
    objective_value: float | None
    constraint_checks: tuple[ConstraintCheck, ...]
    evaluated_candidates: int
    solver_name: str

    def __post_init__(self) -> None:
        if self.evaluated_candidates < 0:
            raise ValueError("evaluated_candidates must be non-negative")
        if not self.solver_name.strip():
            raise ValueError("solver_name must not be empty")
        if self.solution is not None:
            object.__setattr__(self, "solution", MappingProxyType(dict(self.solution)))
        object.__setattr__(self, "constraint_checks", tuple(self.constraint_checks))
