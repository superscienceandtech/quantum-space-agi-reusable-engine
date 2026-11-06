"""Objective and constraint contracts shared by classical solvers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Mapping, Protocol

from .models import ConstraintRelation, ObjectiveSense

Solution = Mapping[str, float]


class Objective(Protocol):
    """A scalar objective evaluated for one complete candidate solution."""

    name: str
    sense: ObjectiveSense

    def evaluate(self, solution: Solution) -> float: ...


class Constraint(Protocol):
    """A scalar expression compared with a bound."""

    name: str

    def check(self, solution: Solution) -> "ConstraintCheck": ...


@dataclass(frozen=True, slots=True)
class ConstraintCheck:
    name: str
    value: float
    relation: ConstraintRelation
    bound: float
    tolerance: float
    feasible: bool
    violation: float


@dataclass(frozen=True, slots=True)
class FunctionalObjective:
    name: str
    sense: ObjectiveSense
    function: Callable[[Solution], float]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("objective name must not be empty")

    def evaluate(self, solution: Solution) -> float:
        value = float(self.function(solution))
        if not isfinite(value):
            raise ValueError(f"objective {self.name!r} returned a non-finite value")
        return value


@dataclass(frozen=True, slots=True)
class FunctionalConstraint:
    name: str
    function: Callable[[Solution], float]
    relation: ConstraintRelation
    bound: float
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("constraint name must not be empty")
        if not isfinite(self.bound):
            raise ValueError("constraint bound must be finite")
        if not isfinite(self.tolerance) or self.tolerance < 0:
            raise ValueError("constraint tolerance must be finite and non-negative")

    def check(self, solution: Solution) -> ConstraintCheck:
        value = float(self.function(solution))
        if not isfinite(value):
            raise ValueError(f"constraint {self.name!r} returned a non-finite value")
        if self.relation is ConstraintRelation.LE:
            raw_violation = value - self.bound
        elif self.relation is ConstraintRelation.GE:
            raw_violation = self.bound - value
        else:
            raw_violation = abs(value - self.bound)
        violation = max(0.0, raw_violation - self.tolerance)
        return ConstraintCheck(self.name, value, self.relation, self.bound, self.tolerance,
                               violation == 0.0, violation)
