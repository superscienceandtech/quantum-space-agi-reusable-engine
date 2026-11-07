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
