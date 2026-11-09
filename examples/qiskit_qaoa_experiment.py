"""Small, seeded QAOA circuit simulation for the synthetic QUBO fixtures.

This uses Qiskit's ideal local statevector sampler, not quantum hardware.
"""

from __future__ import annotations

import json
from itertools import product
from time import perf_counter

if __package__:
    from examples.synthetic_optimization import build_cases, run_qubo_case
else:  # Support direct execution as ``python examples/qiskit_qaoa_experiment.py``.
    from synthetic_optimization import build_cases, run_qubo_case
from quantum_space_agi.optimization import OptimizationStatus
from quantum_space_agi.optimization.qubo import QUBOModel, build_qubo

SEED = 20261112
SHOTS = 512
GRID_SIZE = 7


def _ising_coefficients(
    model: QUBOModel,
) -> tuple[float, dict[int, float], dict[tuple[int, int], float]]:
    """Convert QUBO x bits to H = constant + h.Z + J.ZZ coefficients."""
    positions = {name: index for index, name in enumerate(model.variable_order)}
    h = {index: 0.0 for index in range(len(positions))}
    couplings: dict[tuple[int, int], float] = {}
    constant = model.offset
    for (left, right), coefficient in model.terms.items():
        i, j = positions[left], positions[right]
        if i == j:
            constant += coefficient / 2
            h[i] -= coefficient / 2
        else:
            constant += coefficient / 4
            h[i] -= coefficient / 4
            h[j] -= coefficient / 4
            couplings[(i, j)] = couplings.get((i, j), 0.0) + coefficient / 4
    return constant, h, {pair: value for pair, value in couplings.items() if value}


def _circuit_for_angles(model: QUBOModel, gamma: float, beta: float, scale: float):
    from qiskit import QuantumCircuit

    _, h, couplings = _ising_coefficients(model)
    n = len(model.variable_order)
    circuit = QuantumCircuit(n, n)
    circuit.h(range(n))
    # Cost evolution: exp(-i * gamma * H / scale), with the constant phase omitted.
    for index, coefficient in h.items():
        if coefficient:
            circuit.rz(2 * gamma * coefficient / scale, index)
    for (left, right), coefficient in couplings.items():
        if coefficient:
            circuit.rzz(2 * gamma * coefficient / scale, left, right)
    # One standard transverse-field mixer layer.
    for index in range(n):
        circuit.rx(2 * beta, index)
    circuit.measure(range(n), range(n))
    return circuit


def run_qaoa_case(
    case, *, seed: int = SEED, shots: int = SHOTS, grid_size: int = GRID_SIZE
) -> dict[str, object]:
    """Run a deterministic parameter-grid QAOA simulation and validate its best sample."""
    if shots < 1 or grid_size < 2:
        raise ValueError("shots must be positive and grid_size must be at least 2")
    try:
        from qiskit.primitives import StatevectorSampler
    except ImportError as error:
        raise RuntimeError(
            "Qiskit is required; install the optional extra with "
            "python3 -m pip install -e '.[qiskit-experiment]'"
        ) from error

    model = build_qubo(
        decision_variables=tuple(sorted(case.problem.variables)),
        objective_coefficients={
            name: int(value)
            for name, value in case.objective_counter.coefficients.items()
        },
        objective_sense=case.problem.objective.sense,
        constraints=case.qubo_constraints,
    )
    exact_report = run_qubo_case(case)
    baseline = exact_report["exact_enumerative_baseline"]
    _, h, couplings = _ising_coefficients(model)
    scale = max(
        [abs(value) for value in h.values()]
        + [abs(value) for value in couplings.values()]
        + [1.0]
    )
    sampler = StatevectorSampler(seed=seed, default_shots=shots)
    gamma_grid = [2 * 3.141592653589793 * i / grid_size for i in range(grid_size)]
    beta_grid = [3.141592653589793 * i / grid_size for i in range(grid_size)]

    started = perf_counter()
    best_expected_energy: float | None = None
    best_angles: tuple[float, float] | None = None
    best_counts: dict[str, int] | None = None
    total_shots = 0
    for gamma, beta in product(gamma_grid, beta_grid):
        circuit = _circuit_for_angles(model, gamma, beta, scale)
        sampled = sampler.run([circuit], shots=shots).result()[0].data.c.get_counts()
        counts = dict(sampled)
        expected_energy = (
            sum(
                count * model.energy(bitstring[::-1])
                for bitstring, count in counts.items()
            )
            / shots
        )
        total_shots += sum(counts.values())
        if best_expected_energy is None or expected_energy < best_expected_energy:
            best_expected_energy = expected_energy
            best_angles = (gamma, beta)
            best_counts = counts
    elapsed = perf_counter() - started
    assert (
        best_angles is not None
        and best_counts is not None
        and best_expected_energy is not None
    )

    # Select lowest-energy observed sample in the best-expected-energy distribution.
    bitstring, sample_count = min(
        best_counts.items(), key=lambda item: (model.energy(item[0][::-1]), item[0])
    )
    model_bits = bitstring[::-1]
    energy = model.energy(model_bits)
    decoded = dict(model.decode(model_bits))
    validated = case.problem.validate_solution(decoded)
    checks = tuple(
        constraint.check(validated) for constraint in case.problem.constraints
    )
    feasible = all(check.feasible for check in checks)
    objective_value = case.problem.objective.evaluate(validated) if feasible else None
    exact_status = baseline["status"]
    if exact_status == OptimizationStatus.INFEASIBLE.value and feasible:
        raise AssertionError(
            "simulator sample cannot make the original infeasible problem feasible"
        )

    return {
        "case": case.name,
        "method": "Qiskit StatevectorSampler, ideal local statevector simulation; p=1 QAOA circuit",
        "configuration": {
            "seed": seed,
            "shots_per_parameter_pair": shots,
            "total_shots": total_shots,
            "parameter_grid_size": grid_size,
            "parameter_pairs": grid_size * grid_size,
            "gamma_grid": gamma_grid,
            "beta_grid": beta_grid,
            "selected_gamma": best_angles[0],
            "selected_beta": best_angles[1],
            "cost_hamiltonian_scale": scale,
            "mixer": "Rx(2*beta) on every qubit",
            "circuit_layers": "H on all qubits; one cost unitary; one transverse-field mixer; measure all",
            "bit_order": "Qiskit count string reversed into QUBO variable_order",
        },
        "simulator_result": {
            "sampled_bitstring_qubo_order": model_bits,
            "sample_count_in_selected_distribution": sample_count,
            "qubo_energy": energy,
            "selected_distribution_mean_energy": best_expected_energy,
            "decoded_decision_variables": decoded,
            "feasible": feasible,
            "objective_value": objective_value,
            "constraint_results": [
                {
                    "name": check.name,
                    "value": check.value,
                    "relation": check.relation.value,
                    "bound": check.bound,
                    "feasible": check.feasible,
                    "violation": check.violation,
                }
                for check in checks
            ],
        },
        "exact_qubo_enumeration": exact_report["qubo"],
        "enumerative_solver": baseline,
        "comparison": {
            "feasibility_agrees": (exact_status == OptimizationStatus.OPTIMAL.value)
            == feasible,
            "same_decision_assignment": decoded == baseline["solution"]
            if feasible
            else None,
            "note": "A sampled heuristic may miss the exact optimum; feasibility is checked against the original constraints.",
        },
        "runtime": {
            "method": "time.perf_counter around all parameter-pair circuit submissions and sampling",
            "seconds": elapsed,
            "includes": "circuit construction, statevector simulation, finite-shot sampling, and result collection",
            "excludes": "QUBO construction, exact enumerations, and EnumerativeSolver timing",
        },
    }


def main() -> None:
    cases = build_cases()
    print(
        json.dumps(
            {
                "simulator": "Qiskit StatevectorSampler (ideal local simulator; no hardware)",
                "qiskit_experiments": [run_qaoa_case(case) for case in cases],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
