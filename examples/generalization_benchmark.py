"""Generalization benchmark for deterministic QUBO solver comparisons.

Exact enumeration is an oracle on small instances. SA and dSB receive a
matched QUBO-energy evaluation budget; FG-dSB reports its additional repair
work separately. QAOA statevector results are intentionally kept in a separate
experiment because its simulator workload is not comparable to CPU heuristic
energy-evaluation counts.
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
from dataclasses import dataclass
from itertools import combinations
from math import isclose, isfinite
from pathlib import Path
from random import Random
from statistics import mean, median
from time import perf_counter
from types import MappingProxyType
from typing import Mapping

from quantum_space_agi.optimization import (
    ConstraintRelation,
    EnumerativeSolver,
    FunctionalConstraint,
    FunctionalObjective,
    ObjectiveSense,
    OptimizationProblem,
    OptimizationStatus,
)
from quantum_space_agi.optimization.qubo import (
    LinearConstraintSpec,
    QUBOModel,
    build_qubo,
)
try:
    from examples.qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )
except ImportError:
    from qubo_heuristics import (
        discrete_simulated_bifurcation_qubo,
        feasibility_guided_dsb,
        simulated_annealing_qubo,
    )


DEFAULT_FAMILIES = ("maxcut_sparse", "maxcut_dense", "knapsack")
DEFAULT_SIZES = (8, 12, 16)
DEFAULT_SEED_COUNT = 30
DEFAULT_EVALUATION_BUDGET = 1024
FAMILY_SEED_OFFSETS = {
    "maxcut_sparse": 110_000,
    "maxcut_dense": 220_000,
    "knapsack": 330_000,
}


@dataclass(frozen=True, slots=True)
class BenchmarkInstance:
    """One deterministic problem instance and its QUBO encoding."""

    name: str
    family: str
    size: int
    instance_seed: int
    problem: OptimizationProblem
    qubo: QUBOModel
    linear_constraints: tuple[LinearConstraintSpec, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class PublicMaxCutInstance:
    """Public Max-Cut instance converted exactly to binary QUBO."""

    name: str
    source_path: str
    vertex_count: int
    edge_count: int
    qubo: QUBOModel
    published_reference_energy: float | None

def _add_term(terms: dict[tuple[str, str], float], left: str, right: str, value: float) -> None:
    pair = (left, right) if left <= right else (right, left)
    terms[pair] = terms.get(pair, 0.0) + value


def _build_maxcut_instance(
    family: str, size: int, instance_seed: int
) -> BenchmarkInstance:
    density = 0.25 if family == "maxcut_sparse" else 0.75
    names = tuple(f"x{index:02d}" for index in range(size))
    possible_edges = tuple(combinations(names, 2))
    edge_count = max(1, round(density * len(possible_edges)))
    rng = Random(instance_seed)
    selected_edges = rng.sample(possible_edges, edge_count)
    edges = tuple(
        (left, right, rng.randint(1, 10))
        for left, right in sorted(selected_edges)
    )

    terms: dict[tuple[str, str], float] = {}
    for left, right, weight in edges:
        # QUBO energy equals negative cut weight, so minimizing it maximizes
        # the cut.
        _add_term(terms, left, left, -weight)
        _add_term(terms, right, right, -weight)
        _add_term(terms, left, right, 2 * weight)

    def cut_weight(solution, edge_list=edges) -> float:
        return float(
            sum(weight for left, right, weight in edge_list if solution[left] != solution[right])
        )

    problem = OptimizationProblem(
        objective=FunctionalObjective("max_cut_weight", ObjectiveSense.MAXIMIZE, cut_weight),
        variables={name: (0, 1) for name in names},
    )
    qubo = QUBOModel(
        variable_order=names,
        decision_variables=names,
        terms=terms,
        offset=0.0,
        penalty_coefficient=0,
        slack_variables={},
    )
    return BenchmarkInstance(
        name=f"{family}_n{size:02d}",
        family=family,
        size=size,
        instance_seed=instance_seed,
        problem=problem,
        qubo=qubo,
        linear_constraints=(),
        metadata=MappingProxyType({
            "edge_count": len(edges),
            "possible_edge_count": len(possible_edges),
            "target_density": density,
            "edges": [
                {"left": left, "right": right, "weight": weight}
                for left, right, weight in edges
            ],
        }),
    )


def _build_knapsack_instance(size: int, instance_seed: int) -> BenchmarkInstance:
    rng = Random(instance_seed)
    names = tuple(f"x{index:02d}" for index in range(size))
    values = {name: rng.randint(5, 40) for name in names}
    weights = {name: rng.randint(2, 20) for name in names}
    capacity = max(1, sum(weights.values()) // 2)

    objective = FunctionalObjective(
        "maximize_total_value",
        ObjectiveSense.MAXIMIZE,
        lambda solution, data=values: sum(data[name] * solution[name] for name in data),
    )
    resource_constraint = FunctionalConstraint(
        "weight_capacity",
        lambda solution, data=weights: sum(data[name] * solution[name] for name in data),
        ConstraintRelation.LE,
        capacity,
    )
    problem = OptimizationProblem(
        objective=objective,
        variables={name: (0, 1) for name in names},
        constraints=(resource_constraint,),
    )
    spec = LinearConstraintSpec(
        "weight_capacity", weights, ConstraintRelation.LE, capacity
    )
    qubo = build_qubo(
        decision_variables=names,
        objective_coefficients=values,
        objective_sense=ObjectiveSense.MAXIMIZE,
        constraints=(spec,),
    )
    return BenchmarkInstance(
        name=f"knapsack_n{size:02d}",
        family="knapsack",
        size=size,
        instance_seed=instance_seed,
        problem=problem,
        qubo=qubo,
        linear_constraints=(spec,),
        metadata=MappingProxyType({
            "values": values,
            "weights": weights,
            "capacity": capacity,
            "qubo_variable_count_including_slack": len(qubo.variable_order),
        }),
    )


def build_instance(family: str, size: int, instance_seed: int) -> BenchmarkInstance:
    """Build one fixed-seed sparse/dense Max-Cut or 0/1-knapsack instance."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 4 or size > 20:
        raise ValueError("size must be an integer from 4 through 20; exact-reference cost grows exponentially")
    if isinstance(instance_seed, bool) or not isinstance(instance_seed, int):
        raise ValueError("instance_seed must be an integer")
    if family in ("maxcut_sparse", "maxcut_dense"):
        return _build_maxcut_instance(family, size, instance_seed)
    if family == "knapsack":
        return _build_knapsack_instance(size, instance_seed)
    raise ValueError(f"unsupported benchmark family: {family!r}")


def build_instances(
    families: tuple[str, ...] = DEFAULT_FAMILIES,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
    *,
    instances_per_setting: int = 3,
    instance_seed: int = 20261107,
) -> tuple[BenchmarkInstance, ...]:
    """Create a reproducible cross-product of problem families and sizes."""
    if not families or len(set(families)) != len(families):
        raise ValueError("families must be non-empty and unique")
    if not sizes or len(set(sizes)) != len(sizes):
        raise ValueError("sizes must be non-empty and unique")
    if isinstance(instances_per_setting, bool) or not isinstance(instances_per_setting, int) or instances_per_setting < 1:
        raise ValueError("instances_per_setting must be a positive integer")
    instances = []
    for family in families:
        if family not in FAMILY_SEED_OFFSETS:
            raise ValueError(f"unsupported benchmark family: {family!r}")
        for size in sizes:
            for replicate in range(instances_per_setting):
                derived_seed = (
                    instance_seed + FAMILY_SEED_OFFSETS[family] + size * 100 + replicate
                )
                instances.append(build_instance(family, size, derived_seed))
    return tuple(instances)


def load_public_kipu_maxcut(path: Path, *, published_reference_energy: float | None = None) -> PublicMaxCutInstance:
    """Load the Kipu public Max-Cut Ising JSON format without adding a dependency.

    The source Hamiltonian is constant + sum(h_i*s_i) + sum(J_ij*s_i*s_j).
    With s_i = 1 - 2*x_i, this function constructs a QUBO whose energy is
    exactly the source Hamiltonian energy for every binary assignment.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError("public Max-Cut JSON must be a non-empty object")
    if published_reference_energy is not None and not isfinite(published_reference_energy):
        raise ValueError("published_reference_energy must be finite")

    constant = 0.0
    fields: dict[int, float] = {}
    couplings: dict[tuple[int, int], float] = {}
    vertices: set[int] = set()
    for raw_key, raw_value in raw.items():
        try:
            indices = ast.literal_eval(raw_key)
            value = float(raw_value)
        except (ValueError, TypeError, SyntaxError) as error:
            raise ValueError(f"invalid Ising term {raw_key!r}") from error
        if not isinstance(indices, tuple) or not isfinite(value):
            raise ValueError(f"invalid Ising term {raw_key!r}")
        if len(indices) == 0:
            constant += value
        elif len(indices) == 1:
            (vertex,) = indices
            if isinstance(vertex, bool) or not isinstance(vertex, int) or vertex < 0:
                raise ValueError("Max-Cut vertex ids must be non-negative integers")
            vertices.add(vertex)
            fields[vertex] = fields.get(vertex, 0.0) + value
        elif len(indices) == 2:
            left, right = indices
            if (
                isinstance(left, bool) or not isinstance(left, int) or left < 0
                or isinstance(right, bool) or not isinstance(right, int) or right < 0
                or left == right
            ):
                raise ValueError("Max-Cut edge endpoints must be distinct non-negative integers")
            vertices.update((left, right))
            pair = (left, right) if left < right else (right, left)
            couplings[pair] = couplings.get(pair, 0.0) + value
        else:
            raise ValueError("only constant, linear, and quadratic Ising terms are supported")

    if not vertices:
        raise ValueError("public Max-Cut JSON contains no vertices")
    if vertices != set(range(max(vertices) + 1)):
        raise ValueError("public Max-Cut vertex ids must be contiguous and zero-based")

    names = tuple(f"x{vertex:03d}" for vertex in sorted(vertices))
    name_by_vertex = {vertex: name for vertex, name in enumerate(names)}
    terms: dict[tuple[str, str], float] = {}
    offset = constant
    for vertex, field in fields.items():
        name = name_by_vertex[vertex]
        offset += field
        _add_term(terms, name, name, -2.0 * field)
    for (left, right), coupling in couplings.items():
        left_name, right_name = name_by_vertex[left], name_by_vertex[right]
        offset += coupling
        _add_term(terms, left_name, left_name, -2.0 * coupling)
        _add_term(terms, right_name, right_name, -2.0 * coupling)
        _add_term(terms, left_name, right_name, 4.0 * coupling)

    model = QUBOModel(
        variable_order=names,
        decision_variables=names,
        terms={pair: coefficient for pair, coefficient in terms.items() if coefficient != 0.0},
        offset=offset,
        penalty_coefficient=0,
        slack_variables={},
    )
    return PublicMaxCutInstance(
        name=path.name,
        source_path=str(path),
        vertex_count=len(vertices),
        edge_count=len(couplings),
        qubo=model,
        published_reference_energy=published_reference_energy,
    )


def load_public_gset_maxcut(path: Path, *, best_known_cut: int) -> PublicMaxCutInstance:
    """Load a Stanford Gset edge-list instance and encode energy as ``-cut``.

    Gset vertices are one-indexed in the source file. The returned QUBO uses
    zero-based internal variable names. The best-known cut is a comparison
    target, not an optimality certificate.
    """
    if isinstance(best_known_cut, bool) or not isinstance(best_known_cut, int):
        raise ValueError("best_known_cut must be an integer")
    if best_known_cut < 0:
        raise ValueError("best_known_cut must be non-negative")

    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or len(rows[0]) != 2:
        raise ValueError("Gset file must start with '<vertex_count> <edge_count>'")
    try:
        vertex_count, declared_edge_count = (int(value) for value in rows[0])
    except ValueError as error:
        raise ValueError("Gset header values must be integers") from error
    if vertex_count < 1 or declared_edge_count < 1:
        raise ValueError("Gset vertex and edge counts must be positive")
    if len(rows) - 1 != declared_edge_count:
        raise ValueError("Gset edge count does not match the header")

    names = tuple(f"x{index:03d}" for index in range(vertex_count))
    terms: dict[tuple[str, str], float] = {}
    seen_edges: set[tuple[int, int]] = set()
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != 3:
            raise ValueError(f"Gset edge row {line_number} must contain two vertices and a weight")
        try:
            left, right, weight = (int(value) for value in row)
        except ValueError as error:
            raise ValueError(f"Gset edge row {line_number} must contain integers") from error
        if not (1 <= left <= vertex_count and 1 <= right <= vertex_count) or left == right:
            raise ValueError(f"Gset edge row {line_number} has an invalid endpoint")
        edge = (min(left, right), max(left, right))
        if edge in seen_edges:
            raise ValueError(f"Gset edge row {line_number} duplicates an edge")
        seen_edges.add(edge)

        left_name, right_name = names[left - 1], names[right - 1]
        # A cut edge contributes weight when bits differ. Negating
        # w*(x_i + x_j - 2*x_i*x_j) makes QUBO minimization maximize cut.
        _add_term(terms, left_name, left_name, -float(weight))
        _add_term(terms, right_name, right_name, -float(weight))
        _add_term(terms, left_name, right_name, 2.0 * weight)

    qubo = QUBOModel(
        variable_order=names,
        decision_variables=names,
        terms={pair: coefficient for pair, coefficient in terms.items() if coefficient != 0.0},
        offset=0.0,
        penalty_coefficient=0,
        slack_variables={},
    )
    return PublicMaxCutInstance(
        name=path.stem,
        source_path=str(path),
        vertex_count=vertex_count,
        edge_count=declared_edge_count,
        qubo=qubo,
        published_reference_energy=-float(best_known_cut),
    )


def evaluate_gset_cut(path: Path, bitstring: str) -> int:
    """Recompute a Gset cut directly from its edge list and partition bits.

    This direct objective calculation is independent of the QUBO energy
    conversion and is suitable for checking externally published solutions.
    """
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or len(rows[0]) != 2:
        raise ValueError("Gset file must start with '<vertex_count> <edge_count>'")
    try:
        vertex_count, edge_count = (int(value) for value in rows[0])
    except ValueError as error:
        raise ValueError("Gset header values must be integers") from error
    if len(rows) - 1 != edge_count:
        raise ValueError("Gset edge count does not match the header")
    if len(bitstring) != vertex_count or any(bit not in "01" for bit in bitstring):
        raise ValueError("bitstring must contain one 0/1 character per Gset vertex")

    total = 0
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != 3:
            raise ValueError(f"Gset edge row {line_number} must contain two vertices and a weight")
        try:
            left, right, weight = (int(value) for value in row)
        except ValueError as error:
            raise ValueError(f"Gset edge row {line_number} must contain integers") from error
        if not (1 <= left <= vertex_count and 1 <= right <= vertex_count) or left == right:
            raise ValueError(f"Gset edge row {line_number} has an invalid endpoint")
        if bitstring[left - 1] != bitstring[right - 1]:
            total += weight
    return total

def _quality_record(
    instance: BenchmarkInstance,
    state: Mapping[str, int],
    energy: float,
    *,
    optimal_value: float,
    seed: int,
    runtime_seconds: float,
    energy_evaluations: int,
    repair_evaluations: int = 0,
) -> dict[str, object]:
    decoded = dict(instance.qubo.decode(state))
    candidate = instance.problem.validate_solution(decoded)
    checks = tuple(
        constraint.check(candidate) for constraint in instance.problem.constraints
    )
    feasible = all(check.feasible for check in checks)
    objective = instance.problem.objective.evaluate(candidate) if feasible else None
    gap = None
    relative_gap = None
    if objective is not None:
        raw_gap = (
            optimal_value - objective
            if instance.problem.objective.sense is ObjectiveSense.MAXIMIZE
            else objective - optimal_value
        )
        gap = max(0.0, float(raw_gap))
        relative_gap = gap / max(1.0, abs(optimal_value))
    return {
        "seed": seed,
        "feasible": feasible,
        "objective_value": objective,
        "optimality_gap": gap,
        "relative_optimality_gap": relative_gap,
        "matches_exact_optimum": (
            gap is not None and isclose(gap, 0.0, rel_tol=0.0, abs_tol=1e-12)
        ),
        "qubo_energy": float(energy),
        "energy_evaluations": energy_evaluations,
        "repair_candidates_evaluated": repair_evaluations,
        "runtime_seconds": runtime_seconds,
    }


def _summarize(records: list[dict[str, object]]) -> dict[str, object]:
    gaps = [
        float(record["optimality_gap"])
        for record in records
        if record["optimality_gap"] is not None
    ]
    relative_gaps = [
        float(record["relative_optimality_gap"])
        for record in records
        if record["relative_optimality_gap"] is not None
    ]
    runtimes = [float(record["runtime_seconds"]) for record in records]
    evaluations = [int(record["energy_evaluations"]) for record in records]
    return {
        "runs": len(records),
        "feasible_runs": sum(bool(record["feasible"]) for record in records),
        "feasibility_rate": mean(bool(record["feasible"]) for record in records),
        "optimal_runs": sum(bool(record["matches_exact_optimum"]) for record in records),
        "optimality_rate": mean(bool(record["matches_exact_optimum"]) for record in records),
        "mean_optimality_gap": mean(gaps) if gaps else None,
        "median_optimality_gap": median(gaps) if gaps else None,
        "mean_relative_optimality_gap": mean(relative_gaps) if relative_gaps else None,
        "median_runtime_seconds": median(runtimes),
        "mean_runtime_seconds": mean(runtimes),
        "median_energy_evaluations": median(evaluations),
        "mean_energy_evaluations": mean(evaluations),
        "mean_repair_candidates_evaluated": mean(
            int(record["repair_candidates_evaluated"]) for record in records
        ),
    }


def run_instance(
    instance: BenchmarkInstance,
    *,
    seeds: tuple[int, ...],
    evaluation_budget: int = DEFAULT_EVALUATION_BUDGET,
) -> dict[str, object]:
    """Run paired fixed-seed heuristics against one exact small-instance oracle."""
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be non-empty and unique")
    if isinstance(evaluation_budget, bool) or not isinstance(evaluation_budget, int):
        raise ValueError("evaluation_budget must be an integer")
    if evaluation_budget < 64:
        raise ValueError("evaluation_budget must be at least 64")

    exact_started = perf_counter()
    exact = EnumerativeSolver().solve(instance.problem)
    exact_runtime = perf_counter() - exact_started
    if exact.status is not OptimizationStatus.OPTIMAL or exact.objective_value is None:
        raise RuntimeError(f"{instance.name}: expected a feasible exact reference")

    bit_count = len(instance.qubo.variable_order)
    sa_restarts = min(4, max(1, evaluation_budget // (2 * bit_count)))
    sa_sweeps = max(
        1, (evaluation_budget - sa_restarts) // (sa_restarts * bit_count)
    )
    dsb_agents = min(8, max(1, evaluation_budget // 2))
    dsb_steps = max(1, evaluation_budget // dsb_agents)

    records: dict[str, list[dict[str, object]]] = {
        "simulated_annealing": [],
        "discrete_sb": [],
    }
    if instance.linear_constraints:
        records["fg_dsb"] = []

    for seed in seeds:
        started = perf_counter()
        sa = simulated_annealing_qubo(
            instance.qubo,
            seed=seed,
            sweeps=sa_sweeps,
            restarts=sa_restarts,
        )
        sa_runtime = perf_counter() - started
        records["simulated_annealing"].append(
            _quality_record(
                instance, sa.state, sa.energy,
                optimal_value=exact.objective_value,
                seed=seed, runtime_seconds=sa_runtime,
                energy_evaluations=sa.proposals_evaluated + sa_restarts,
            )
        )

        started = perf_counter()
        dsb = discrete_simulated_bifurcation_qubo(
            instance.qubo, seed=seed, agents=dsb_agents, steps=dsb_steps
        )
        dsb_runtime = perf_counter() - started
        records["discrete_sb"].append(
            _quality_record(
                instance, dsb.state, dsb.energy,
                optimal_value=exact.objective_value,
                seed=seed, runtime_seconds=dsb_runtime,
                energy_evaluations=dsb.updates_evaluated,
            )
        )

        if instance.linear_constraints:
            started = perf_counter()
            fg = feasibility_guided_dsb(
                instance.qubo,
                instance.problem,
                instance.linear_constraints,
                seed=seed,
                agents=dsb_agents,
                steps=dsb_steps,
                max_flip_size=2,
            )
            fg_runtime = perf_counter() - started
            records["fg_dsb"].append(
                _quality_record(
                    instance, fg.state, fg.energy,
                    optimal_value=exact.objective_value,
                    seed=seed, runtime_seconds=fg_runtime,
                    energy_evaluations=dsb_agents * dsb_steps,
                    repair_evaluations=fg.repair_candidates_evaluated,
                )
            )

    exact_record = {
        "status": exact.status.value,
        "objective_value": exact.objective_value,
        "evaluated_candidates": exact.evaluated_candidates,
        "runtime_seconds": exact_runtime,
        "role": "exact oracle; reference cost is reported separately from matched heuristic budgets",
    }
    return {
        "instance": {
            "name": instance.name,
            "family": instance.family,
            "decision_variable_count": instance.size,
            "qubo_variable_count": bit_count,
            "instance_seed": instance.instance_seed,
            "metadata": dict(instance.metadata),
        },
        "protocol": {
            "solver_seeds": seeds,
            "requested_energy_evaluation_budget": evaluation_budget,
            "sa_restarts": sa_restarts,
            "sa_sweeps_per_restart": sa_sweeps,
            "sa_energy_evaluation_budget_including_initial_states": (
                sa_restarts + sa_restarts * sa_sweeps * bit_count
            ),
            "dsb_agents": dsb_agents,
            "dsb_steps": dsb_steps,
            "dsb_energy_evaluation_budget": dsb_agents * dsb_steps,
            "fg_dsb_repair_neighborhood": "all one- and two-decision-bit flips",
        },
        "exact_reference": exact_record,
        "methods": {
            name: {
                "summary": _summarize(method_records),
                "runs": method_records,
            }
            for name, method_records in records.items()
        },
    }


def run_benchmark(
    *,
    families: tuple[str, ...] = DEFAULT_FAMILIES,
    sizes: tuple[int, ...] = DEFAULT_SIZES,
    instances_per_setting: int = 3,
    seed_count: int = DEFAULT_SEED_COUNT,
    seed_start: int = 0,
    evaluation_budget: int = DEFAULT_EVALUATION_BUDGET,
    instance_seed: int = 20261107,
) -> dict[str, object]:
    if isinstance(seed_count, bool) or not isinstance(seed_count, int) or seed_count < 1:
        raise ValueError("seed_count must be a positive integer")
    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    seeds = tuple(range(seed_start, seed_start + seed_count))
    instances = build_instances(
        families,
        sizes,
        instances_per_setting=instances_per_setting,
        instance_seed=instance_seed,
    )
    return {
        "benchmark": "QUBO heuristic generalization pilot",
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "design": {
            "families": families,
            "sizes": sizes,
            "instances_per_setting": instances_per_setting,
            "instance_seed_base": instance_seed,
            "paired_solver_seeds": seeds,
            "requested_energy_evaluation_budget_per_run": evaluation_budget,
            "exact_reference_max_size": max(sizes),
            "limitations": [
                "Synthetic generated instances; no public benchmark suite included yet.",
                "Exact solver is an oracle and is not compared under the heuristic budget.",
                "FG-dSB repair work is reported separately and exceeds the base dSB budget.",
                "QAOA StatevectorSampler remains a separate simulator experiment; its cost is not directly comparable to CPU heuristic energy evaluations.",
                "Wall-clock measurements depend on the host and are not hardware-advantage evidence.",
            ],
        },
        "results": [
            run_instance(
                instance, seeds=seeds, evaluation_budget=evaluation_budget
            )
            for instance in instances
        ],
    }


def run_public_maxcut_instance(
    instance: PublicMaxCutInstance,
    *,
    reference_energy: float,
    seeds: tuple[int, ...],
    evaluation_budget: int = DEFAULT_EVALUATION_BUDGET,
    reference_interpretation: str = (
        "Upstream publishes this as a ground-state energy; this run does not independently certify optimality."
    ),
) -> dict[str, object]:
    """Compare SA and sparse dSB to a published energy reference, not an exact oracle."""
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be non-empty and unique")
    if not isfinite(reference_energy):
        raise ValueError("reference_energy must be finite")
    if isinstance(evaluation_budget, bool) or not isinstance(evaluation_budget, int) or evaluation_budget < 64:
        raise ValueError("evaluation_budget must be an integer of at least 64")

    bit_count = len(instance.qubo.variable_order)
    sa_restarts = min(2, max(1, evaluation_budget // (2 * bit_count)))
    sa_sweeps = max(1, (evaluation_budget - sa_restarts) // (sa_restarts * bit_count))
    dsb_agents = min(8, max(1, evaluation_budget // 2))
    dsb_steps = max(1, evaluation_budget // dsb_agents)
    records: dict[str, list[dict[str, object]]] = {
        "simulated_annealing": [],
        "discrete_sb": [],
    }

    for seed in seeds:
        started = perf_counter()
        sa = simulated_annealing_qubo(
            instance.qubo,
            seed=seed,
            sweeps=sa_sweeps,
            restarts=sa_restarts,
        )
        sa_runtime = perf_counter() - started
        sa_gap = sa.energy - reference_energy
        records["simulated_annealing"].append({
            "seed": seed,
            "energy": sa.energy,
            "gap_to_published_reference": sa_gap,
            "matches_published_reference": abs(sa_gap) <= 1e-8,
            "below_published_reference": sa_gap < -1e-8,
            "energy_evaluations": sa.proposals_evaluated + sa_restarts,
            "runtime_seconds": sa_runtime,
        })

        started = perf_counter()
        dsb = discrete_simulated_bifurcation_qubo(
            instance.qubo,
            seed=seed,
            agents=dsb_agents,
            steps=dsb_steps,
        )
        dsb_runtime = perf_counter() - started
        dsb_gap = dsb.energy - reference_energy
        records["discrete_sb"].append({
            "seed": seed,
            "energy": dsb.energy,
            "gap_to_published_reference": dsb_gap,
            "matches_published_reference": abs(dsb_gap) <= 1e-8,
            "below_published_reference": dsb_gap < -1e-8,
            "energy_evaluations": dsb.updates_evaluated,
            "runtime_seconds": dsb_runtime,
        })

    method_results = {}
    for name, method_records in records.items():
        gaps = [float(record["gap_to_published_reference"]) for record in method_records]
        energies = [float(record["energy"]) for record in method_records]
        runtimes = [float(record["runtime_seconds"]) for record in method_records]
        method_results[name] = {
            "summary": {
                "runs": len(method_records),
                "reference_match_rate": mean(bool(r["matches_published_reference"]) for r in method_records),
                "below_reference_runs": sum(bool(r["below_published_reference"]) for r in method_records),
                "best_energy": min(energies),
                "mean_energy": mean(energies),
                "mean_gap_to_reference": mean(gaps),
                "median_gap_to_reference": median(gaps),
                "median_runtime_seconds": median(runtimes),
                "mean_runtime_seconds": mean(runtimes),
                "mean_energy_evaluations": mean(int(r["energy_evaluations"]) for r in method_records),
            },
            "runs": method_records,
        }

    return {
        "instance": {
            "name": instance.name,
            "source_path": instance.source_path,
            "vertex_count": instance.vertex_count,
            "edge_count": instance.edge_count,
            "qubo_variable_count": bit_count,
        },
        "reference": {
            "published_energy": reference_energy,
            "interpretation": reference_interpretation,
        },
        "protocol": {
            "paired_solver_seeds": seeds,
            "requested_energy_evaluation_budget": evaluation_budget,
            "sa_restarts": sa_restarts,
            "sa_sweeps_per_restart": sa_sweeps,
            "sa_energy_evaluations_per_run": sa_restarts + sa_restarts * sa_sweeps * bit_count,
            "dsb_agents": dsb_agents,
            "dsb_steps": dsb_steps,
            "d_sb_updates_per_run": dsb_agents * dsb_steps,
        },
        "methods": method_results,
    }

def _csv_ints(value: str, label: str) -> tuple[int, ...]:
    try:
        parsed = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"{label} must be comma-separated integers") from error
    if not parsed:
        raise argparse.ArgumentTypeError(f"{label} must not be empty")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--families",
        default=",".join(DEFAULT_FAMILIES),
        help="comma-separated: maxcut_sparse,maxcut_dense,knapsack",
    )
    parser.add_argument("--sizes", default="8,12,16", help="comma-separated decision-variable counts")
    parser.add_argument("--instances-per-setting", type=int, default=3)
    parser.add_argument("--instance-seed", type=int, default=20261107)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--evaluation-budget", type=int, default=DEFAULT_EVALUATION_BUDGET)
    parser.add_argument("--public-maxcut-json", type=Path)
    parser.add_argument("--public-reference-energy", type=float)
    parser.add_argument("--public-gset-file", type=Path)
    parser.add_argument("--gset-best-known-cut", type=int)
    parser.add_argument("--gset-certificate-json", type=Path)
    parser.add_argument("--gset-certificate-key")
    parser.add_argument("--skip-generated", action="store_true")
    parser.add_argument("--output", type=Path, help="optional JSON output file; stdout if omitted")
    args = parser.parse_args()

    has_public_input = args.public_maxcut_json is not None or args.public_gset_file is not None
    if args.skip_generated and not has_public_input:
        parser.error("--skip-generated requires a public instance input")
    if (args.public_maxcut_json is None) != (args.public_reference_energy is None):
        parser.error("--public-maxcut-json and --public-reference-energy must be provided together")
    if (args.public_gset_file is None) != (args.gset_best_known_cut is None):
        parser.error("--public-gset-file and --gset-best-known-cut must be provided together")
    if args.gset_certificate_json is not None and args.public_gset_file is None:
        parser.error("--gset-certificate-json requires --public-gset-file")
    if args.gset_certificate_key is not None and args.gset_certificate_json is None:
        parser.error("--gset-certificate-key requires --gset-certificate-json")

    families = tuple(part.strip() for part in args.families.split(",") if part.strip())
    sizes = _csv_ints(args.sizes, "sizes")
    generated = None
    if not args.skip_generated:
        generated = run_benchmark(
            families=families,
            sizes=sizes,
            instances_per_setting=args.instances_per_setting,
            seed_count=args.seed_count,
            instance_seed=args.instance_seed,
            seed_start=args.seed_start,
            evaluation_budget=args.evaluation_budget,
        )

    seeds = tuple(range(args.seed_start, args.seed_start + args.seed_count))
    public = None
    if args.public_maxcut_json is not None:
        instance = load_public_kipu_maxcut(args.public_maxcut_json)
        public = run_public_maxcut_instance(
            instance,
            reference_energy=args.public_reference_energy,
            seeds=seeds,
            evaluation_budget=args.evaluation_budget,
        )
    public_gset = None
    if args.public_gset_file is not None:
        gset_instance = load_public_gset_maxcut(
            args.public_gset_file,
            best_known_cut=args.gset_best_known_cut,
        )
        public_gset = run_public_maxcut_instance(
            gset_instance,
            reference_energy=gset_instance.published_reference_energy,
            seeds=seeds,
            evaluation_budget=args.evaluation_budget,
            reference_interpretation=(
                "Upstream best-known cut converted to negative QUBO energy; "
                "this run does not independently certify optimality."
            ),
        )
        if args.gset_certificate_json is not None:
            certificate_doc = json.loads(args.gset_certificate_json.read_text(encoding="utf-8"))
            try:
                certificate_key = args.gset_certificate_key or gset_instance.name
                certificate = certificate_doc["solutions"][certificate_key]
                certificate_bits = certificate["bits"]
                certificate_cut = certificate["cut"]
                certificate_vertices = certificate["N"]
            except (KeyError, TypeError) as error:
                parser.error(f"invalid Gset certificate JSON for {certificate_key}: {error}")
            if certificate_vertices != gset_instance.vertex_count:
                parser.error("Gset certificate vertex count does not match the graph")
            recomputed_cut = evaluate_gset_cut(args.public_gset_file, certificate_bits)
            if recomputed_cut != certificate_cut:
                parser.error(
                    f"Gset certificate cut mismatch: declared {certificate_cut}, "
                    f"recomputed {recomputed_cut}"
                )
            public_gset["solution_certificate_check"] = {
                "source": str(args.gset_certificate_json),
                "declared_cut": certificate_cut,
                "recomputed_cut": recomputed_cut,
                "matches": True,
                "interpretation": "This validates an attainable cut value, not global optimality.",
            }
    report = {
        "generated_benchmark": generated,
        "public_maxcut_benchmark": public,
        "public_gset_benchmark": public_gset,
    }
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output is None:
        print(serialized)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Wrote benchmark report to {args.output}")


if __name__ == "__main__":
    main()
