import math
from pathlib import Path

import nbformat
import numpy as np
import pytest
from pydantic import ValidationError

from quantum_space_agi.simulation import (
    OrbitalState,
    SimulationConfig,
    diagnose_trajectory,
    interpolate_collision_event,
    propagate_two_body,
    rk4_step,
    run_simulation,
    two_body_derivative,
)
from quantum_space_agi.simulation.models import EARTH_MU_M3_S2, EARTH_REFERENCE_RADIUS_M


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "notebooks" / "arc05_simulation"


def execute_notebook(notebook_name):
    namespace = {"__name__": "arc05_integration_test"}
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, f"{notebook_name}:code-cell", "exec"), namespace)
    return namespace


def example_config(**overrides):
    values = {
        "initial_position_m": (7_000_000.0, 0.0, 0.0),
        "initial_velocity_mps": (0.0, 7_500.0, 0.0),
        "simulation_duration_s": 600.0,
        "time_step_s": 10.0,
        "collision_radius_m": EARTH_REFERENCE_RADIUS_M,
    }
    values.update(overrides)
    return SimulationConfig(**values)


def test_package_workflow_contract_is_deterministic_and_float64():
    config = example_config()
    first = run_simulation(config)
    second = run_simulation(config)

    assert np.array_equal(first["times_s"], second["times_s"])
    assert np.array_equal(first["states"], second["states"])
    assert np.array_equal(
        first["diagnostics"]["specific_energy_m2_s2"],
        second["diagnostics"]["specific_energy_m2_s2"],
    )
    assert first["states"].dtype == np.float64
    assert first["times_s"].dtype == np.float64
    assert first["model"]["reference_frame"] == "ECI"
    assert first["model"]["integrator"] == "RK4"
    assert first["model"]["dynamics"].startswith("Earth point-mass")


def test_package_propagation_matches_notebook_propagation():
    notebook = execute_notebook("05_orbital_propagation.ipynb")
    initial = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64)
    notebook_result = notebook["propagate_two_body"](
        initial,
        EARTH_MU_M3_S2,
        600.0,
        10.0,
        EARTH_REFERENCE_RADIUS_M,
    )
    package_result = propagate_two_body(
        initial,
        EARTH_MU_M3_S2,
        600.0,
        10.0,
        EARTH_REFERENCE_RADIUS_M,
    )

    assert np.array_equal(notebook_result["times_s"], package_result["times_s"])
    assert np.array_equal(notebook_result["states"], package_result["states"])
    assert notebook_result["collision_index"] == package_result["collision_index"]
    assert notebook_result["collision_time_s"] == package_result["collision_time_s"]
    assert notebook_result["collision_method"] == package_result["collision_method"]


def test_notebook_and_package_rk4_match():
    notebook = execute_notebook("04_rk4_integrator.ipynb")
    state = np.array([1.0], dtype=np.float64)

    notebook_value = state.copy()
    package_value = state.copy()
    for index in range(10):
        notebook_value = notebook["rk4_step"](
            notebook_value,
            index / 10.0,
            0.1,
            notebook["linear_derivative"],
            1.0,
        )
        package_value = rk4_step(
            package_value,
            index / 10.0,
            0.1,
            lambda _time, y, slope: slope * y,
            1.0,
        )
    assert np.array_equal(notebook_value, package_value)


def test_rk4_does_not_mutate_input():
    state = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64)
    original = state.copy()
    result = rk4_step(
        state,
        0.0,
        10.0,
        lambda _time, y, mu: two_body_derivative(y, mu),
        EARTH_MU_M3_S2,
    )
    assert np.array_equal(state, original)
    assert result.dtype == np.float64
    assert result.shape == (6,)


def test_initial_state_collision_is_exact():
    result = propagate_two_body(
        np.array([6_000_000.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64),
        EARTH_MU_M3_S2,
        600.0,
        10.0,
        EARTH_REFERENCE_RADIUS_M,
    )
    assert result["collision_index"] == 0
    assert result["collision_time_s"] == 0.0
    assert result["collision_method"] == "exact_sample"
    assert np.array_equal(result["collision_state"], result["states"][0])
    assert len(result["times_s"]) == 1


def test_collision_interpolation_requires_bracket():
    previous = np.array([6_400_000.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    following = np.array([6_300_000.0, 0.0, 0.0, 1.0, 0.0, 0.0], dtype=np.float64)
    event_time, event_state, method = interpolate_collision_event(
        0.0,
        previous,
        10.0,
        following,
        6_378_137.0,
    )
    assert method == "linear_radius_interpolation"
    assert 0.0 < event_time < 10.0
    assert abs(np.linalg.norm(event_state[:3]) - 6_378_137.0) < 1.0


def test_collision_interpolation_rejects_nonbracket():
    previous = np.array([6_000_000.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    following = np.array([6_100_000.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    with pytest.raises(ValueError, match="threshold is not bracketed"):
        interpolate_collision_event(
            0.0,
            previous,
            10.0,
            following,
            6_378_137.0,
        )


def test_shortened_final_step_ends_exactly_at_duration():
    result = propagate_two_body(
        np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64),
        EARTH_MU_M3_S2,
        605.0,
        100.0,
        EARTH_REFERENCE_RADIUS_M,
    )
    assert result["times_s"][-1] == 605.0
    assert result["times_s"][1] - result["times_s"][0] == 100.0
    assert result["times_s"][-1] - result["times_s"][-2] == 5.0


def test_trajectory_diagnostics_are_matched_and_finite():
    result = run_simulation(example_config(simulation_duration_s=600.0))
    diagnostics = result["diagnostics"]
    count = result["states"].shape[0]
    for key in (
        "specific_energy_m2_s2",
        "specific_angular_momentum_m2_s",
        "eccentricity_magnitude",
        "radius_m",
        "speed_m_s",
        "energy_drift_m2_s2",
        "angular_momentum_drift_m2_s",
    ):
        assert diagnostics[key].shape == (count,)
        assert np.all(np.isfinite(diagnostics[key]))
    assert math.isfinite(diagnostics["max_abs_energy_drift_m2_s2"])
    assert math.isfinite(diagnostics["max_abs_angular_momentum_drift_m2_s"])


def test_orbital_state_round_trip_is_float64():
    array = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64)
    state = OrbitalState.from_array(array, 3.5)
    assert state.to_array().dtype == np.float64
    assert np.array_equal(state.to_array(), array)
    assert state.time_s == 3.5


@pytest.mark.parametrize(
    "value",
    [
        [1, 2, 3, 4, 5],
        [1, 2, 3, 4, 5, 6, 7],
        [1, 2, 3, 4, 5, float("nan")],
        [1, 2, 3, 4, 5, float("inf")],
        ["1", 2, 3, 4, 5, 6],
        [True, 2, 3, 4, 5, 6],
        [1 + 0j, 2, 3, 4, 5, 6],
        np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64),
    ],
)
def test_orbital_state_rejects_invalid_vectors(value):
    with pytest.raises(ValueError):
        OrbitalState.from_array(value, 0.0)


@pytest.mark.parametrize(
    "overrides",
    [
        {"simulation_duration_s": 0.0},
        {"simulation_duration_s": -1.0},
        {"simulation_duration_s": float("nan")},
        {"simulation_duration_s": float("inf")},
        {"time_step_s": 0.0},
        {"time_step_s": -1.0},
        {"collision_radius_m": 0.0},
        {"collision_radius_m": float("inf")},
        {"gravitational_parameter_m3_s2": 0.0},
        {"integrator": "Euler"},
        {"reference_frame": "ECEF"},
        {"unknown_option": True},
    ],
)
def test_configuration_rejects_invalid_inputs(overrides):
    with pytest.raises((ValidationError, ValueError)):
        example_config(**overrides)


@pytest.mark.parametrize("time_s", [-1.0, float("nan"), float("inf"), True, "0"])
def test_orbital_state_rejects_invalid_time(time_s):
    vector = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64)
    with pytest.raises(ValueError):
        OrbitalState.from_array(vector, time_s)


@pytest.mark.parametrize("initial_time", ["0", True, float("nan"), float("inf")])
def test_workflow_rejects_invalid_initial_time(initial_time):
    with pytest.raises(ValueError, match="Initial time"):
        run_simulation(example_config(), initial_time_s=initial_time)


def test_nonfinite_derivative_and_invalid_stage_are_rejected():
    with pytest.raises(ValueError, match="Position radius"):
        two_body_derivative(
            np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64),
            EARTH_MU_M3_S2,
        )
    with pytest.raises(ValueError, match="RK4 intermediate stage"):
        rk4_step(
            np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64),
            0.0,
            1.0,
            lambda _time, state: np.array([float("nan")] * state.size),
        )
