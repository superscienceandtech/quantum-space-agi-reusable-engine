"""Small classical heuristic baselines for QUBO experiment evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite
from random import Random
from types import MappingProxyType
from typing import Mapping

from quantum_space_agi.optimization.qubo import QUBOModel


@dataclass(frozen=True, slots=True)
class AnnealingResult:
    """Best state visited by one seeded simulated-annealing run."""

    state: Mapping[str, int]
    energy: float
    proposals_evaluated: int
    accepted_moves: int
    seed: int


def simulated_annealing_qubo(
    model: QUBOModel,
    *,
    seed: int,
    sweeps: int = 64,
    restarts: int = 4,
    initial_temperature: float = 10.0,
    final_temperature: float = 0.05,
) -> AnnealingResult:
    """Minimize a QUBO with seeded single-bit Metropolis updates.

    This is a classical heuristic. It is neither a quantum annealer nor a
    quantum-inspired algorithm, and it provides no optimality guarantee.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if isinstance(sweeps, bool) or not isinstance(sweeps, int) or sweeps < 1:
        raise ValueError("sweeps must be a positive integer")
    if isinstance(restarts, bool) or not isinstance(restarts, int) or restarts < 1:
        raise ValueError("restarts must be a positive integer")
    if not isfinite(initial_temperature) or initial_temperature <= 0:
        raise ValueError("initial_temperature must be finite and positive")
    if not isfinite(final_temperature) or final_temperature <= 0:
        raise ValueError("final_temperature must be finite and positive")
    if final_temperature > initial_temperature:
        raise ValueError("final_temperature must not exceed initial_temperature")

    rng = Random(seed)
    names = model.variable_order
    number_of_bits = len(names)
    total_proposals = sweeps * number_of_bits
    best_state: list[int] | None = None
    best_energy: float | None = None
    proposals = 0
    accepted = 0

    for _ in range(restarts):
        current = [rng.randrange(2) for _ in names]
        current_energy = model.energy(dict(zip(names, current)))
        if best_energy is None or current_energy < best_energy:
            best_state, best_energy = current.copy(), current_energy

        for step in range(total_proposals):
            fraction = step / max(1, total_proposals - 1)
            temperature = initial_temperature * (
                final_temperature / initial_temperature
            ) ** fraction
            candidate = current.copy()
            candidate[rng.randrange(number_of_bits)] ^= 1
            candidate_energy = model.energy(dict(zip(names, candidate)))
            proposals += 1

            if best_energy is None or candidate_energy < best_energy:
                best_state, best_energy = candidate.copy(), candidate_energy
            delta = candidate_energy - current_energy
            if delta <= 0 or rng.random() < exp(-delta / temperature):
                current, current_energy = candidate, candidate_energy
                accepted += 1

    assert best_state is not None and best_energy is not None
    return AnnealingResult(
        state=MappingProxyType(dict(zip(names, best_state))),
        energy=best_energy,
        proposals_evaluated=proposals,
        accepted_moves=accepted,
        seed=seed,
    )

from quantum_space_agi.optimization.models import ConstraintRelation, OptimizationProblem
from quantum_space_agi.optimization.qubo import LinearConstraintSpec


@dataclass(frozen=True, slots=True)
class BifurcationResult:
    """Best QUBO state visited by one discrete simulated-bifurcation run."""

    state: Mapping[str, int]
    energy: float
    agents: int
    steps: int
    updates_evaluated: int
    seed: int


@dataclass(frozen=True, slots=True)
class FeasibilityGuidedResult:
    """Result of dSB followed by original-constraint-guided local repair."""

    initial_state: Mapping[str, int]
    state: Mapping[str, int]
    initial_energy: float
    energy: float
    feasible: bool
    objective_value: float | None
    violations: Mapping[str, float]
    repair_moves: int
    repair_candidates_evaluated: int
    seed: int


def qubo_to_ising(model: QUBOModel) -> tuple[float, tuple[float, ...], tuple[tuple[float, ...], ...]]:
    """Return constant, fields, and symmetric pair couplings for spins in {-1,+1}.

    Uses b_i = (1 - s_i) / 2 and the convention
    E(s) = constant + sum_i h_i*s_i + sum_{i<j} J_ij*s_i*s_j.
    The returned representation is checked against QUBO energy in tests.
    """
    names = model.variable_order
    positions = {name: index for index, name in enumerate(names)}
    fields = [0.0] * len(names)
    couplings = [[0.0] * len(names) for _ in names]
    constant = model.offset
    for (left, right), coefficient in model.terms.items():
        i, j = positions[left], positions[right]
        if i == j:
            constant += coefficient / 2.0
            fields[i] -= coefficient / 2.0
        else:
            constant += coefficient / 4.0
            fields[i] -= coefficient / 4.0
            fields[j] -= coefficient / 4.0
            couplings[i][j] += coefficient / 4.0
            couplings[j][i] += coefficient / 4.0
    return constant, tuple(fields), tuple(tuple(row) for row in couplings)


def discrete_simulated_bifurcation_qubo(
    model: QUBOModel,
    *,
    seed: int,
    agents: int = 8,
    steps: int = 96,
    time_step: float = 0.05,
    a0: float = 1.0,
    pump_end: float = 2.0,
    c0: float = 1.0,
) -> BifurcationResult:
    """Run a small CPU reference implementation of discrete SB (dSB).

    This is a quantum-inspired classical heuristic, not a quantum solver. The
    integrator follows the symplectic-Euler dSB update; independent agents are
    evaluated sequentially in this portable reference implementation.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if isinstance(agents, bool) or not isinstance(agents, int) or agents < 1:
        raise ValueError("agents must be a positive integer")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    if not isfinite(time_step) or time_step <= 0:
        raise ValueError("time_step must be finite and positive")
    if not isfinite(a0) or a0 <= 0 or not isfinite(pump_end) or pump_end <= a0:
        raise ValueError("pump_end and a0 must be finite, positive, and pump_end > a0")
    if not isfinite(c0) or c0 <= 0:
        raise ValueError("c0 must be finite and positive")

    _, raw_fields, raw_couplings = qubo_to_ising(model)
    scale = max(
        [abs(value) for value in raw_fields]
        + [abs(raw_couplings[i][j]) for i in range(len(raw_fields)) for j in range(i + 1, len(raw_fields))]
        + [1.0]
    )
    fields = tuple(value / scale for value in raw_fields)
    couplings = tuple(tuple(value / scale for value in row) for row in raw_couplings)
    names = model.variable_order
    rng = Random(seed)
    best_state: dict[str, int] | None = None
    best_energy: float | None = None
    updates = 0

    for _ in range(agents):
        position = [rng.uniform(-1e-3, 1e-3) for _ in names]
        momentum = [0.0] * len(names)
        for step in range(steps):
            pump = pump_end * (step + 1) / steps
            spins = [1 if value >= 0 else -1 for value in position]
            next_momentum = [0.0] * len(names)
            next_position = [0.0] * len(names)
            for i in range(len(names)):
                force = -fields[i] - sum(
                    couplings[i][j] * spins[j]
                    for j in range(len(names))
                    if j != i
                )
                next_momentum[i] = momentum[i] + (
                    (pump - a0) * position[i] + c0 * force
                ) * time_step
                next_position[i] = position[i] + a0 * next_momentum[i] * time_step
                if abs(next_position[i]) > 1.0:
                    next_position[i] = 1.0 if next_position[i] > 0 else -1.0
                    next_momentum[i] = 0.0

            position, momentum = next_position, next_momentum
            state = {
                name: (0 if position[index] >= 0 else 1)
                for index, name in enumerate(names)
            }
            energy = model.energy(state)
            updates += 1
            if best_energy is None or energy < best_energy:
                best_state, best_energy = state, energy

    assert best_state is not None and best_energy is not None
    return BifurcationResult(
        state=MappingProxyType(best_state),
        energy=best_energy,
        agents=agents,
        steps=steps,
        updates_evaluated=updates,
        seed=seed,
    )


def feasibility_guided_dsb(
    model: QUBOModel,
    problem: "OptimizationProblem",
    constraints: tuple["LinearConstraintSpec", ...],
    *,
    seed: int,
    agents: int = 8,
    steps: int = 96,
    max_flip_size: int = 2,
) -> FeasibilityGuidedResult:
    """Project-specific hybrid: dSB proposal plus feasible-first bit-flip repair.

    Repair ranks candidates lexicographically by violated-constraint count,
    normalized total violation, then the original objective. It searches all
    one- and two-decision-bit flips, re-encodes integer slack exactly, and stops
    when no strictly better neighbor exists. This is an experimental design;
    literature novelty and general performance are not established.
    """
    from itertools import combinations

    from quantum_space_agi.optimization.models import ObjectiveSense

    decision_names = tuple(sorted(problem.variables))
    if any(tuple(problem.variables[name]) != (0.0, 1.0) for name in decision_names):
        raise ValueError("feasibility_guided_dsb currently requires binary (0, 1) domains")
    if not constraints:
        raise ValueError("linear constraint specifications are required for slack encoding")
    if isinstance(max_flip_size, bool) or not isinstance(max_flip_size, int) or max_flip_size < 1:
        raise ValueError("max_flip_size must be a positive integer")
    max_flip_size = min(max_flip_size, len(decision_names))

    initial = discrete_simulated_bifurcation_qubo(
        model, seed=seed, agents=agents, steps=steps
    )
    current = {name: int(value) for name, value in model.decode(initial.state).items()}

    def assess(candidate_bits: Mapping[str, int]):
        validated = problem.validate_solution(candidate_bits)
        checks = tuple(constraint.check(validated) for constraint in problem.constraints)
        objective = problem.objective.evaluate(validated)
        violated = sum(not check.feasible for check in checks)
        normalized = sum(
            check.violation / max(1.0, abs(check.bound), abs(check.value))
            for check in checks
        )
        objective_rank = (
            -objective if problem.objective.sense is ObjectiveSense.MAXIMIZE else objective
        )
        return (violated, normalized, objective_rank), checks, objective

    def encode_slacks(candidate_bits: Mapping[str, int]) -> dict[str, int]:
        encoded = {name: int(candidate_bits[name]) for name in decision_names}
        for spec in constraints:
            lhs = sum(spec.coefficients.get(name, 0) * encoded[name] for name in decision_names)
            if spec.relation is ConstraintRelation.LE:
                slack = max(0, spec.bound - lhs)
            elif spec.relation is ConstraintRelation.GE:
                slack = max(0, lhs - spec.bound)
            else:
                slack = 0
            for index, slack_name in enumerate(model.slack_variables.get(spec.name, ())):
                encoded[slack_name] = (slack >> index) & 1
        if set(encoded) != set(model.variable_order):
            raise ValueError("constraint specs do not match the QUBO slack variables")
        return encoded

    current_key, current_checks, current_objective = assess(current)
    repair_moves = 0
    candidates_evaluated = 0
    while True:
        best_bits = None
        best_key = current_key
        best_checks = current_checks
        best_objective = current_objective
        for flip_size in range(1, max_flip_size + 1):
            for flipped in combinations(decision_names, flip_size):
                neighbor = dict(current)
                for name in flipped:
                    neighbor[name] = 1 - neighbor[name]
                key, checks, objective = assess(neighbor)
                candidates_evaluated += 1
                if key < best_key:
                    best_bits, best_key = neighbor, key
                    best_checks, best_objective = checks, objective
        if best_bits is None:
            break
        current = best_bits
        current_key, current_checks, current_objective = best_key, best_checks, best_objective
        repair_moves += 1

    final_state = encode_slacks(current)
    feasible = all(check.feasible for check in current_checks)
    return FeasibilityGuidedResult(
        initial_state=MappingProxyType(dict(initial.state)),
        state=MappingProxyType(final_state),
        initial_energy=initial.energy,
        energy=model.energy(final_state),
        feasible=feasible,
        objective_value=current_objective if feasible else None,
        violations=MappingProxyType({check.name: check.violation for check in current_checks}),
        repair_moves=repair_moves,
        repair_candidates_evaluated=candidates_evaluated,
        seed=seed,
    )
