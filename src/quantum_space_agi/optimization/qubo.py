"""QUBO encoding for small integer linear problems over binary variables.

This module builds an energy function only. It does not run quantum hardware
or provide a quantum solver; examples use classical bitstring enumeration.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from .models import ConstraintRelation, ObjectiveSense


@dataclass(frozen=True, slots=True)
class LinearConstraintSpec:
    """Integer-coefficient linear constraint over binary decision variables."""

    name: str
    coefficients: Mapping[str, int]
    relation: ConstraintRelation
    bound: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("constraint name must not be empty")
        if isinstance(self.bound, bool) or not isinstance(self.bound, int):
            raise ValueError("QUBO constraint bounds must be integers")
        if not isinstance(self.relation, ConstraintRelation):
            raise ValueError("relation must be a ConstraintRelation")
        copied: dict[str, int] = {}
        for name, value in self.coefficients.items():
            if not name.strip():
                raise ValueError("constraint variable names must not be empty")
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("QUBO constraint coefficients must be integers")
            copied[name] = value
        object.__setattr__(self, "coefficients", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class QUBOModel:
    """Energy ``offset + sum(Q[i,j] * bit[i] * bit[j])``.

    Variable order is stable and is also the order used by string bitstrings.
    Decoding returns only original decision variables, excluding slack bits.
    """

    variable_order: tuple[str, ...]
    decision_variables: tuple[str, ...]
    terms: Mapping[tuple[str, str], float]
    offset: float
    penalty_coefficient: int
    slack_variables: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if len(set(self.variable_order)) != len(self.variable_order):
            raise ValueError("QUBO variable names must be unique")
        if not set(self.decision_variables).issubset(self.variable_order):
            raise ValueError("decision variables must be included in variable_order")
        if not isfinite(self.offset):
            raise ValueError("QUBO offset must be finite")
        for (left, right), coefficient in self.terms.items():
            if left not in self.variable_order or right not in self.variable_order:
                raise ValueError("QUBO term references an unknown variable")
            if left > right:
                raise ValueError("QUBO term keys must be in canonical lexical order")
            if not isfinite(coefficient):
                raise ValueError("QUBO coefficients must be finite")
        object.__setattr__(self, "terms", MappingProxyType(dict(self.terms)))
        object.__setattr__(
            self,
            "slack_variables",
            MappingProxyType({name: tuple(items) for name, items in self.slack_variables.items()}),
        )

    def _normalize_bits(self, state: str | Mapping[str, int]) -> Mapping[str, int]:
        if isinstance(state, str):
            if len(state) != len(self.variable_order) or any(bit not in "01" for bit in state):
                raise ValueError("bitstring must contain one 0/1 character per QUBO variable")
            bits = dict(zip(self.variable_order, (int(bit) for bit in state)))
        else:
            bits = dict(state)
            if set(bits) != set(self.variable_order):
                raise ValueError("bit mapping must contain exactly the QUBO variables")
            if any(not isinstance(bit, (int, bool)) or bit not in (0, 1) for bit in bits.values()):
                raise ValueError("QUBO bits must be integers 0 or 1")
        return MappingProxyType(bits)

    def energy(self, state: str | Mapping[str, int]) -> float:
        """Evaluate energy for one complete bitstring or bit mapping."""
        bits = self._normalize_bits(state)
        return self.offset + sum(
            coefficient * bits[left] * bits[right]
            for (left, right), coefficient in self.terms.items()
        )

    def decode(self, state: str | Mapping[str, int]) -> Mapping[str, int]:
        """Decode the original decision bits; constraint feasibility is separate."""
        bits = self._normalize_bits(state)
        return MappingProxyType({name: bits[name] for name in self.decision_variables})

    def decode_slacks(self, state: str | Mapping[str, int]) -> Mapping[str, int]:
        """Return each integer slack value represented by its binary bits."""
        bits = self._normalize_bits(state)
        return MappingProxyType(
            {
                constraint: sum((1 << index) * bits[name] for index, name in enumerate(names))
                for constraint, names in self.slack_variables.items()
            }
        )


def build_qubo(
    decision_variables: tuple[str, ...],
    objective_coefficients: Mapping[str, int],
    objective_sense: ObjectiveSense,
    constraints: tuple[LinearConstraintSpec, ...],
    *,
    penalty_coefficient: int | None = None,
) -> QUBOModel:
    """Convert an integer linear binary model into quadratic unconstrained energy.

    The objective's binary range is ``sum(abs(c_i))``. Integer constraint
    residuals have a minimum nonzero magnitude of one. The default penalty is
    objective range + 1, so one violated equality penalty outweighs any possible
    improvement across the full objective range.
    """
    decision_variables = tuple(decision_variables)
    if not decision_variables or len(set(decision_variables)) != len(decision_variables):
        raise ValueError("decision_variables must be non-empty and unique")
    variable_set = set(decision_variables)
    if any(not name.strip() for name in decision_variables):
        raise ValueError("decision variable names must not be empty")
    if set(objective_coefficients) != variable_set:
        raise ValueError("objective coefficients must define every decision variable exactly once")
    if not isinstance(objective_sense, ObjectiveSense):
        raise ValueError("objective_sense must be an ObjectiveSense")
    if any(isinstance(c, bool) or not isinstance(c, int) for c in objective_coefficients.values()):
        raise ValueError("QUBO objective coefficients must be integers")
    if len({constraint.name for constraint in constraints}) != len(constraints):
        raise ValueError("constraint names must be unique in a QUBO encoding")
    for constraint in constraints:
        if not set(constraint.coefficients).issubset(variable_set):
            raise ValueError(f"constraint {constraint.name!r} references an unknown decision variable")

    objective_range = sum(abs(value) for value in objective_coefficients.values())
    penalty = objective_range + 1 if penalty_coefficient is None else penalty_coefficient
    if isinstance(penalty, bool) or not isinstance(penalty, int) or penalty <= objective_range:
        raise ValueError(f"penalty_coefficient must be an integer greater than {objective_range}")

    variable_order = list(decision_variables)
    slack_variables: dict[str, tuple[str, ...]] = {}
    slack_signs: dict[str, int] = {}
    for constraint in constraints:
        lower = sum(min(0, coefficient) for coefficient in constraint.coefficients.values())
        upper = sum(max(0, coefficient) for coefficient in constraint.coefficients.values())
        if constraint.relation is ConstraintRelation.LE:
            max_slack, slack_sign = constraint.bound - lower, 1
        elif constraint.relation is ConstraintRelation.GE:
            max_slack, slack_sign = upper - constraint.bound, -1
        else:
            max_slack, slack_sign = 0, 0
        names: list[str] = []
        if constraint.relation is not ConstraintRelation.EQ and max_slack > 0:
            for index in range(max_slack.bit_length()):
                name = f"__slack__{constraint.name}__{index}"
                if name in variable_order:
                    raise ValueError(f"generated slack variable name collision: {name}")
                variable_order.append(name)
                names.append(name)
                slack_signs[name] = slack_sign * (1 << index)
        slack_variables[constraint.name] = tuple(names)

    terms: dict[tuple[str, str], float] = {}
    offset = 0.0

    def add_term(left: str, right: str, value: float) -> None:
        pair = (left, right) if left <= right else (right, left)
        terms[pair] = terms.get(pair, 0.0) + value

    sense_factor = 1 if objective_sense is ObjectiveSense.MINIMIZE else -1
    for name, coefficient in objective_coefficients.items():
        add_term(name, name, float(sense_factor * coefficient))

    position = {name: index for index, name in enumerate(variable_order)}
    for constraint in constraints:
        residual_coefficients = {
            name: float(coefficient)
            for name, coefficient in constraint.coefficients.items()
            if coefficient != 0
        }
        for slack_name in slack_variables[constraint.name]:
            residual_coefficients[slack_name] = float(slack_signs[slack_name])
        constant = float(-constraint.bound)
        offset += penalty * constant * constant
        names = sorted(residual_coefficients, key=position.__getitem__)
        for index, left in enumerate(names):
            left_value = residual_coefficients[left]
            # For bits, b_i^2 == b_i; cross terms in a square carry factor 2.
            add_term(left, left, penalty * (2 * constant * left_value + left_value**2))
            for right in names[index + 1 :]:
                add_term(left, right, penalty * 2 * left_value * residual_coefficients[right])

    return QUBOModel(
        variable_order=tuple(variable_order),
        decision_variables=decision_variables,
        terms={pair: value for pair, value in terms.items() if value != 0.0},
        offset=offset,
        penalty_coefficient=penalty,
        slack_variables=slack_variables,
    )
