import math
import re
from pathlib import Path

import nbformat
import numpy as np
import pytest
from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "notebooks" / "arc05_simulation"
NOTEBOOK_NAMES = [
    "01_simulation_configuration.ipynb",
    "02_orbital_state.ipynb",
    "03_two_body_dynamics.ipynb",
    "04_rk4_integrator.ipynb",
    "05_orbital_propagation.ipynb",
    "06_simulation_diagnostics.ipynb",
    "07_orbital_validation.ipynb",
]


def execute_notebook(namespace, notebook_name):
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            exec(compile(cell.source, f"{notebook_name}:code-cell", "exec"), namespace)
    return namespace


@pytest.fixture(scope="module")
def notebook_namespaces():
    namespaces = {}
    for name in NOTEBOOK_NAMES:
        namespace = {"__name__": f"arc05_test_{name[:2]}"}
        execute_notebook(namespace, name)
        namespaces[name] = namespace
    return namespaces


def _stored_text_output(notebook_name):
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    text_parts = []
    for cell in notebook.cells:
        for output in getattr(cell, "outputs", []):
            if output.output_type == "stream":
                text_parts.append("".join(output.get("text", [])))
            elif output.output_type in ("execute_result", "display_data"):
                text_parts.append(str(output.get("data", {}).get("text/plain", "")))
    return "\n".join(text_parts)


def test_stable_rk4_output_matches_current_source(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[3]]
    text = _stored_text_output(NOTEBOOK_NAMES[3])
    for steps in (1, 10, 100):
        y = np.array([1.0], dtype=np.float64)
        dt = 1.0 / steps
        for index in range(steps):
            y = ns["rk4_step"](y, index * dt, dt, ns["linear_derivative"], 1.0)
        match = re.search(rf"steps=\s*{steps}\s+value=([0-9.]+)", text)
        assert match is not None
        assert float(match.group(1)) == pytest.approx(y[0], abs=5e-13)


def test_stable_orbital_output_matches_current_source(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    text = _stored_text_output(NOTEBOOK_NAMES[6])
    match = re.search(r"Circular period \(analytic\): ([0-9.]+)", text)
    assert match is not None
    mu = ns["MU"]
    expected_period = 2.0 * math.pi * math.sqrt(7_000_000.0**3 / mu)
    assert float(match.group(1)) == pytest.approx(expected_period, rel=1e-12)

    match = re.search(r"Elliptical period: ([0-9.]+)", text)
    assert match is not None
    expected_semi_major = 8_000_000.0
    expected_elliptical_period = 2.0 * math.pi * math.sqrt(expected_semi_major**3 / mu)
    assert float(match.group(1)) == pytest.approx(expected_elliptical_period, rel=1e-12)

    match = re.search(r"Return-position error with 20 s RK4 steps: ([0-9.e+-]+) m", text)
    assert match is not None
    assert abs(float(match.group(1)) - ns["position_error"]) < 1e-6


@pytest.mark.parametrize("notebook_name", NOTEBOOK_NAMES)
def test_notebook_is_valid_json_and_executes_notebook_cells(notebook_name, notebook_namespaces):
    assert notebook_namespaces[notebook_name]
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    assert notebook.nbformat == 4
    assert any(cell.cell_type == "code" for cell in notebook.cells)


@pytest.mark.parametrize("notebook_name", NOTEBOOK_NAMES)
def test_notebook_has_stored_execution_output(notebook_name):
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    assert any(getattr(cell, "outputs", None) for cell in notebook.cells)


def test_configuration_defaults_and_si_contract(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[0]]
    config = ns["example_config"]
    assert config.reference_frame == "ECI"
    assert config.integrator == "RK4"
    assert config.gravitational_parameter_m3_s2 == 3.986004418e14
    assert config.collision_radius_m == 6_378_137.0
    assert config.simulation_duration_s == 600.0
    assert config.time_step_s == 10.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"initial_position_m": (1.0, 2.0)},
        {"initial_velocity_mps": (1.0, 2.0)},
        {"initial_position_m": ("7000000", 0.0, 0.0)},
        {"initial_velocity_mps": (False, 0.0, 0.0)},
        {"initial_position_m": (1j, 0.0, 0.0)},
        {"simulation_duration_s": float("nan")},
        {"simulation_duration_s": float("inf")},
        {"simulation_duration_s": 0.0},
        {"simulation_duration_s": -1.0},
        {"time_step_s": float("nan")},
        {"time_step_s": float("inf")},
        {"time_step_s": 0.0},
        {"time_step_s": -1.0},
        {"collision_radius_m": 0.0},
        {"collision_radius_m": -1.0},
        {"collision_radius_m": float("nan")},
        {"collision_radius_m": float("inf")},
        {"gravitational_parameter_m3_s2": 0.0},
        {"gravitational_parameter_m3_s2": True},
        {"integrator": "Euler"},
        {"reference_frame": "ECEF"},
        {"unknown_option": True},
    ],
)
def test_configuration_rejects_invalid_inputs(notebook_namespaces, overrides):
    ns = notebook_namespaces[NOTEBOOK_NAMES[0]]
    data = ns["example_config"].model_dump()
    data.update(overrides)
    with pytest.raises((ValidationError, ValueError)):
        ns["SimulationConfig"](**data)


def test_configuration_is_frozen(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[0]]
    with pytest.raises(ValidationError):
        ns["example_config"].time_step_s = 20.0


def test_orbital_state_round_trip_and_float64(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[1]]
    state = ns["OrbitalState"].from_array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], 3.5)
    array = state.to_array()
    assert array.dtype == np.float64
    assert array.shape == (6,)
    assert state.time_s == 3.5
    assert np.array_equal(ns["OrbitalState"].from_array(array, 3.5).to_array(), array)


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
        [[1], 2, 3, 4, 5, 6],
        np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64),
    ],
)
def test_orbital_state_rejects_invalid_vectors(notebook_namespaces, value):
    ns = notebook_namespaces[NOTEBOOK_NAMES[1]]
    with pytest.raises(ValueError):
        ns["OrbitalState"].from_array(value, 0.0)


@pytest.mark.parametrize("time_s", [-1.0, float("nan"), float("inf"), True, "0"])
def test_orbital_state_rejects_invalid_time(notebook_namespaces, time_s):
    ns = notebook_namespaces[NOTEBOOK_NAMES[1]]
    vector = [7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0]
    with pytest.raises(ValueError):
        ns["OrbitalState"].from_array(vector, time_s)


def test_two_body_derivative_position_and_velocity_contract(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[2]]
    state = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0])
    derivative = ns["two_body_derivative"](state, ns["EARTH_MU_M3_S2"])
    assert derivative.shape == (6,)
    assert np.allclose(derivative[:3], state[3:])
    assert np.isclose(derivative[3], -ns["EARTH_MU_M3_S2"] / 7_000_000.0**2)
    assert np.allclose(derivative[4:], 0.0)


@pytest.mark.parametrize(
    "notebook_name,derivative_name",
    [
        (NOTEBOOK_NAMES[2], "two_body_derivative"),
        (NOTEBOOK_NAMES[6], "strict_derivative"),
    ],
)
def test_two_body_derivatives_reject_tiny_radius_and_overflow_acceleration(
    notebook_namespaces, notebook_name, derivative_name
):
    ns = notebook_namespaces[notebook_name]
    mu = ns["EARTH_MU_M3_S2"] if notebook_name == NOTEBOOK_NAMES[2] else ns["MU"]
    args = (mu,) if notebook_name == NOTEBOOK_NAMES[2] else (0.0, mu)
    if notebook_name == NOTEBOOK_NAMES[2]:
        with pytest.raises(ValueError):
            ns[derivative_name](np.array([1e-300, 0, 0, 0, 0, 0]), mu)
    else:
        with pytest.raises(ValueError):
            ns[derivative_name](0.0, np.array([1e-300, 0, 0, 0, 0, 0]), mu)


@pytest.mark.parametrize(
    "notebook_name,derivative_name",
    [
        (NOTEBOOK_NAMES[2], "two_body_derivative"),
        (NOTEBOOK_NAMES[6], "strict_derivative"),
    ],
)
def test_two_body_derivatives_reject_acceleration_underflow_without_suppressing_warnings(
    notebook_namespaces, notebook_name, derivative_name
):
    ns = notebook_namespaces[notebook_name]
    mu = ns["EARTH_MU_M3_S2"] if notebook_name == NOTEBOOK_NAMES[2] else ns["MU"]
    state = np.array([1e308, 1e308, 1e308, 0, 0, 0], dtype=np.float64)
    with pytest.raises(ValueError, match="underflows|invalid|non-finite|radius"):
        if notebook_name == NOTEBOOK_NAMES[2]:
            ns[derivative_name](state, mu)
        else:
            ns[derivative_name](0.0, state, mu)


@pytest.mark.parametrize(
    "mu",
    [0.0, -1.0, float("nan"), float("inf"), True, "398600441800000"],
)
def test_two_body_derivative_rejects_invalid_mu(notebook_namespaces, mu):
    ns = notebook_namespaces[NOTEBOOK_NAMES[2]]
    with pytest.raises(ValueError):
        ns["two_body_derivative"]([7_000_000.0, 0, 0, 0, 7_500, 0], mu)


@pytest.mark.parametrize(
    "state",
    [
        [1, 2, 3, 4, 5],
        [1, 2, 3, 4, 5, 6, 7],
        [0, 0, 0, 0, 0, 0],
        [float("nan"), 0, 0, 0, 0, 0],
        [float("inf"), 0, 0, 0, 0, 0],
        ["1", 2, 3, 4, 5, 6],
        [True, 2, 3, 4, 5, 6],
        [1 + 0j, 2, 3, 4, 5, 6],
        [[1], 2, 3, 4, 5, 6],
    ],
)
def test_two_body_derivative_rejects_invalid_states(notebook_namespaces, state):
    ns = notebook_namespaces[NOTEBOOK_NAMES[2]]
    with pytest.raises(ValueError):
        ns["two_body_derivative"](state, ns["EARTH_MU_M3_S2"])


def test_rk4_exponential_reference_and_fourth_order_ratios(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[3]]
    initial = np.array([1.0], dtype=np.float64)
    errors = []
    for dt in (0.2, 0.1, 0.05, 0.025):
        steps = round(1.0 / dt)
        y = initial.copy()
        actual_dt = 1.0 / steps
        for index in range(steps):
            y = ns["rk4_step"](y, index * actual_dt, actual_dt, ns["linear_derivative"], 1.0)
        errors.append(abs(y[0] - math.e))
    assert all(fine < coarse for coarse, fine in zip(errors, errors[1:]))
    ratios = [coarse / fine for coarse, fine in zip(errors, errors[1:])]
    assert all(ratio > 8.0 for ratio in ratios)
    assert all(12.0 < ratio < 32.0 for ratio in ratios)


def test_rk4_does_not_mutate_state(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[3]]
    original = np.array([1.0])
    result = ns["rk4_step"](original, 0.0, 0.1, ns["linear_derivative"], 1.0)
    assert np.array_equal(original, np.array([1.0]))
    assert result.dtype == np.float64


def test_rk4_rejects_nonfinite_and_wrong_shape_intermediate_stages(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[3]]
    state = np.array([1.0], dtype=np.float64)

    def nonfinite_derivative(_time, _state, *_args):
        return np.array([float("inf")])

    def wrong_shape_derivative(_time, _state, *_args):
        return np.array([1.0, 2.0])

    with pytest.raises(ValueError):
        ns["rk4_step"](state, 0.0, 0.1, nonfinite_derivative)
    with pytest.raises(ValueError):
        ns["rk4_step"](state, 0.0, 0.1, wrong_shape_derivative)


@pytest.mark.parametrize(
    "time_s,dt,state",
    [
        (0.0, 0.0, np.array([1.0])),
        (0.0, -1.0, np.array([1.0])),
        (0.0, float("nan"), np.array([1.0])),
        (0.0, float("inf"), np.array([1.0])),
        (0.0, True, np.array([1.0])),
        (0.0, "0.1", np.array([1.0])),
        (float("nan"), 0.1, np.array([1.0])),
        (0.0, 0.1, np.array([])),
        (0.0, 0.1, np.array([float("nan")])),
        (0.0, 0.1, np.array([1 + 0j])),
        (0.0, 0.1, [[1.0]]),
        (0.0, 0.1, [True]),
        (0.0, 0.1, ["1"]),
    ],
)
def test_rk4_rejects_invalid_inputs(notebook_namespaces, time_s, dt, state):
    ns = notebook_namespaces[NOTEBOOK_NAMES[3]]
    with pytest.raises(ValueError):
        ns["rk4_step"](state, time_s, dt, ns["linear_derivative"], 1.0)


def test_propagation_partial_timestep_and_shape(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    mu = ns["mu"]
    radius = ns["radius"]
    initial = np.array([radius, 0, 0, 0, np.sqrt(mu / radius), 0], dtype=np.float64)
    trajectory = ns["propagate_two_body"](initial, mu, 25.0, 10.0, 6_378_137.0)
    assert np.array_equal(trajectory["times_s"], np.array([0.0, 10.0, 20.0, 25.0]))
    assert trajectory["states"].shape == (4, 6)
    assert trajectory["states"].dtype == np.float64
    assert trajectory["collision_index"] is None


def test_propagation_initial_collision_is_not_silently_changed(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    collision_radius = 6_378_137.0
    initial = np.array([collision_radius, 0, 0, 0, 0, 0], dtype=np.float64)
    trajectory = ns["propagate_two_body"](initial, ns["mu"], 100.0, 1.0, collision_radius)
    assert trajectory["collision_index"] == 0
    assert trajectory["collision_radius_m"] == collision_radius
    assert trajectory["states"].shape[0] == 1


def test_propagation_collision_between_samples_is_interpolated(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    mu = ns["mu"]
    radius = 6_378_137.0
    initial = np.array([radius + 1000.0, 0, 0, -2000.0, 0, 0], dtype=np.float64)
    trajectory = ns["propagate_two_body"](initial, mu, 2.0, 1.0, radius)
    assert trajectory["collision_index"] == 1
    assert trajectory["collision_time_s"] is not None
    assert 0.0 < trajectory["collision_time_s"] <= 1.0
    assert trajectory["collision_method"] == "linear_radius_interpolation"
    assert np.linalg.norm(trajectory["collision_state"][:3]) == pytest.approx(radius, rel=1e-4)
    assert np.linalg.norm(trajectory["states"][trajectory["collision_index"], :3]) <= radius
    assert trajectory["states"][-1, 0] <= radius


def test_propagation_exact_collision_sample_and_no_false_positive(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    mu = ns["mu"]
    radius = 6_378_137.0
    inside = np.array([radius, 0, 0, 0, 0, 0], dtype=np.float64)
    initial_inside = ns["propagate_two_body"](inside, mu, 10.0, 1.0, radius)
    assert initial_inside["collision_index"] == 0
    assert initial_inside["collision_time_s"] == 0.0
    assert initial_inside["collision_method"] == "exact_sample"

    exact_time, exact_state, exact_method = ns["interpolate_collision_event"](
        0.0,
        np.array([radius, 0, 0, 0, 0, 0], dtype=np.float64),
        1.0,
        np.array([radius - 1.0, 0, 0, 0, 0, 0], dtype=np.float64),
        radius,
    )
    assert exact_time == 0.0
    assert np.linalg.norm(exact_state[:3]) == radius
    assert exact_method == "exact_sample"

    outside = np.array([7_000_000.0, 0, 0, 0, math.sqrt(mu / 7_000_000.0), 0], dtype=np.float64)
    clear = ns["propagate_two_body"](outside, mu, 100.0, 10.0, radius)
    assert clear["collision_index"] is None
    assert clear["collision_time_s"] is None
    assert clear["collision_state"] is None


def test_collision_bracket_both_endpoints_outside_is_rejected(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    with pytest.raises(ValueError, match="threshold is not bracketed"):
        ns["interpolate_collision_event"](
            0.0,
            np.array([9.0, 0, 0, 0, 100, 0], dtype=np.float64),
            1.0,
            np.array([8.0, 0, 0, 0, 90, 0], dtype=np.float64),
            7.0,
        )


def test_collision_bracket_both_endpoints_inside_is_rejected(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    with pytest.raises(ValueError, match="threshold is not bracketed"):
        ns["interpolate_collision_event"](
            0.0,
            np.array([6.0, 0, 0, 0, 100, 0], dtype=np.float64),
            1.0,
            np.array([5.0, 0, 0, 0, 90, 0], dtype=np.float64),
            7.0,
        )


def test_collision_bracket_valid_crossing_interpolation(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    ns_07 = notebook_namespaces[NOTEBOOK_NAMES[6]]
    event_time, event_state, method = ns["interpolate_collision_event"](
        0.0,
        np.array([10.0, 0, 0, 100, 20, 0], dtype=np.float64),
        2.0,
        np.array([4.0, 0, 0, 40, 10, 0], dtype=np.float64),
        7.0,
    )
    assert event_time == pytest.approx(1.0)
    assert method == "linear_radius_interpolation"
    assert event_state.shape == (6,)
    assert np.all(np.isfinite(event_state))
    assert event_state[:3].tolist() == pytest.approx([7.0, 0, 0])

    event_time_07, event_state_07, method_07 = ns_07["linear_radius_collision_event"](
        0.0,
        np.array([10.0, 0, 0, 100, 20, 0], dtype=np.float64),
        2.0,
        np.array([4.0, 0, 0, 40, 10, 0], dtype=np.float64),
        7.0,
    )
    assert event_time_07 == pytest.approx(event_time)
    assert method_07 == method
    assert event_state_07.tolist() == pytest.approx(event_state.tolist())


def test_collision_valid_ascending_crossing_interpolation(notebook_namespaces):
    ns_05 = notebook_namespaces[NOTEBOOK_NAMES[4]]
    ns_07 = notebook_namespaces[NOTEBOOK_NAMES[6]]
    previous = np.array([4.0, 0, 0, 40, 10, 0], dtype=np.float64)
    next_y = np.array([10.0, 0, 0, 100, 20, 0], dtype=np.float64)

    event_time, event_state, method = ns_05["interpolate_collision_event"](
        0.0, previous, 2.0, next_y, 7.0
    )
    assert event_time == pytest.approx(1.0)
    assert method == "linear_radius_interpolation"
    assert event_state[:3].tolist() == pytest.approx([7.0, 0, 0])

    event_time_07, event_state_07, method_07 = ns_07["linear_radius_collision_event"](
        0.0, previous, 2.0, next_y, 7.0
    )
    assert event_time_07 == pytest.approx(event_time)
    assert method_07 == method
    assert event_state_07.tolist() == pytest.approx(event_state.tolist())


def test_collision_exact_endpoint_contact_remains_exact_sample(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    event_time, event_state, method = ns["interpolate_collision_event"](
        0.0,
        np.array([10.0, 0, 0, 0, 0, 0], dtype=np.float64),
        1.0,
        np.array([7.0, 0, 0, 2, 0, 0], dtype=np.float64),
        7.0,
    )
    assert event_time == 1.0
    assert np.linalg.norm(event_state[:3]) == 7.0
    assert method == "exact_sample"


def test_collision_oblique_3d_interpolation_is_radial_estimate(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    previous = np.array([8.0, 6.0, 0.0, 10.0, 20.0, 30.0], dtype=np.float64)
    next_y = np.array([0.0, 4.0, 5.0, 20.0, 10.0, 5.0], dtype=np.float64)
    event_time, event_state, method = ns["interpolate_collision_event"](
        0.0, previous, 3.0, next_y, 7.0
    )
    previous_radius = np.linalg.norm(previous[:3])
    next_radius = np.linalg.norm(next_y[:3])
    alpha = (7.0 - previous_radius) / (next_radius - previous_radius)
    assert event_time == pytest.approx(alpha * 3.0)
    assert method == "linear_radius_interpolation"
    assert event_state.tolist() == pytest.approx(((1.0 - alpha) * previous + alpha * next_y).tolist())


@pytest.mark.parametrize(
    "previous_radius,next_radius",
    [
        (9.0, 9.0),
        (8.0, 8.0),
    ],
)
def test_collision_degenerate_intervals_are_rejected(notebook_namespaces, previous_radius, next_radius):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    with pytest.raises(ValueError, match="degenerate"):
        ns["interpolate_collision_event"](
            0.0,
            np.array([previous_radius, 0, 0, 0, 0, 0], dtype=np.float64),
            1.0,
            np.array([next_radius, 0, 0, 0, 0, 0], dtype=np.float64),
            7.0,
        )


@pytest.mark.parametrize(
    "args",
    [
        ([1, 2, 3], 3.986004418e14, 1.0, 0.1, 6_378_137.0),
        ([0, 0, 0, 0, 0, 0], 3.986004418e14, 1.0, 0.1, 6_378_137.0),
        ([1, 2, 3, 4, 5, float("nan")], 3.986004418e14, 1.0, 0.1, 6_378_137.0),
        ([7_000_000, 0, 0, 0, 7_500, 0], 0.0, 1.0, 0.1, 6_378_137.0),
        ([7_000_000, 0, 0, 0, 7_500, 0], 3.986004418e14, float("inf"), 0.1, 6_378_137.0),
        ([7_000_000, 0, 0, 0, 7_500, 0], 3.986004418e14, 1.0, True, 6_378_137.0),
        ([7_000_000, 0, 0, 0, 7_500, 0], 3.986004418e14, 1.0, 0.1, 0.0),
    ],
)
def test_propagation_rejects_invalid_inputs(notebook_namespaces, args):
    ns = notebook_namespaces[NOTEBOOK_NAMES[4]]
    with pytest.raises((ValueError, OverflowError)):
        ns["propagate_two_body"](*args)


def test_diagnostics_circular_reference_is_exact_for_repeated_state(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[5]]
    mu = ns["mu"]
    radius = ns["radius"]
    speed = math.sqrt(mu / radius)
    circular = np.array([radius, 0, 0, 0, speed, 0], dtype=np.float64)
    _, h_magnitude = ns["specific_angular_momentum"](circular)
    _, eccentricity = ns["eccentricity_vector"](circular, mu)
    times = np.array([0.0, 1.0, 2.0])
    states = np.vstack((circular, circular, circular))
    diagnostics = ns["diagnose_trajectory"](times, states, mu)
    assert np.isclose(h_magnitude, radius * speed, rtol=1e-12, atol=1e-8)
    assert eccentricity < 1e-10
    assert diagnostics["energy_drift_m2_s2"].tolist() == [0.0, 0.0, 0.0]
    assert diagnostics["angular_momentum_drift_m2_s"].tolist() == [0.0, 0.0, 0.0]


@pytest.mark.parametrize(
    "state",
    [
        [1, 2, 3],
        [0, 0, 0, 0, 0, 0],
        [1, 2, 3, 4, 5, "6"],
        [1, 2, 3, 4, 5, float("nan")],
        [1, 2, 3, 4, 5, float("inf")],
        [True, 2, 3, 4, 5, 6],
        [1 + 0j, 2, 3, 4, 5, 6],
    ],
)
def test_diagnostics_reject_invalid_states(notebook_namespaces, state):
    ns = notebook_namespaces[NOTEBOOK_NAMES[5]]
    with pytest.raises(ValueError):
        ns["specific_orbital_energy"](state, ns["mu"])


@pytest.mark.parametrize(
    "times,states",
    [
        ([0.0], [[1, 2, 3, 4, 5]]),
        ([0.0, -1.0], [[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]]),
        ([0.0, 1.0], [[1, 2, 3, 4, 5, 6]]),
        ([0.0, 1.0], [[1, 2, 3, 4, 5, float("nan")], [1, 2, 3, 4, 5, 6]]),
    ],
)
def test_diagnostics_reject_invalid_trajectories(notebook_namespaces, times, states):
    ns = notebook_namespaces[NOTEBOOK_NAMES[5]]
    with pytest.raises(ValueError):
        ns["diagnose_trajectory"](times, states, ns["mu"])


def test_validation_circular_period_and_position_return(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    radius = 7_000_000.0
    speed = math.sqrt(mu / radius)
    initial = np.array([radius, 0, 0, 0, speed, 0], dtype=np.float64)
    period = 2.0 * math.pi * math.sqrt(radius**3 / mu)
    times, states, collision = ns["propagate"](initial, period, 20.0)
    error = float(np.linalg.norm(states[-1, :3] - initial[:3]))
    assert times[-1] == period
    assert collision is None
    assert error < 10_000.0


def test_validation_elliptical_reference_and_partial_end_time(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    semi_major_axis = 8_000_000.0
    periapsis = 7_000_000.0
    speed = math.sqrt(mu * (2.0 / periapsis - 1.0 / semi_major_axis))
    initial = np.array([periapsis, 0, 0, 0, speed, 0], dtype=np.float64)
    times, states, collision = ns["propagate"](initial, 1000.0, 10.0)
    eccentricity = 1.0 - periapsis / semi_major_axis
    assert 0.0 < eccentricity < 1.0
    assert times[-1] == 1000.0
    assert states.shape == (101, 6)
    assert collision is None


@pytest.mark.parametrize("dt", [60.0, 30.0, 15.0])
def test_validation_energy_and_angular_momentum_drift_is_bounded(notebook_namespaces, dt):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    radius = 7_000_000.0
    speed = math.sqrt(mu / radius)
    initial = np.array([radius, 0, 0, 0, speed, 0], dtype=np.float64)
    period = 2.0 * math.pi * math.sqrt(radius**3 / mu)
    _, states, collision = ns["propagate"](initial, period, dt)
    assert collision is None
    energies = np.array([ns["orbital_energy"](state, mu) for state in states])
    angular_momenta = np.array([ns["angular_momentum_magnitude"](state) for state in states])
    relative_energy_drift = np.max(np.abs(energies - energies[0])) / abs(energies[0])
    relative_angular_drift = np.max(np.abs(angular_momenta - angular_momenta[0])) / angular_momenta[0]
    if dt == 60.0:
        assert relative_energy_drift < 2e-5
        assert relative_angular_drift < 2e-6
    elif dt == 30.0:
        assert relative_energy_drift < 1e-6
        assert relative_angular_drift < 1e-7
    else:
        assert relative_energy_drift < 1e-7
        assert relative_angular_drift < 1e-9


def test_validation_timestep_sensitivity_converges(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    radius = 7_000_000.0
    initial = np.array([radius, 0, 0, 0, np.sqrt(mu / radius), 0], dtype=np.float64)
    period = 2.0 * math.pi * math.sqrt(radius**3 / mu)
    errors = {}
    for dt in (60.0, 30.0, 15.0):
        _, states, _ = ns["propagate"](initial, period, dt)
        errors[dt] = float(np.linalg.norm(states[-1, :3] - initial[:3]))
    assert errors[60.0] > errors[30.0] > errors[15.0]
    ratios = [errors[60.0] / errors[30.0], errors[30.0] / errors[15.0]]
    assert all(12.0 < ratio < 64.0 for ratio in ratios)


def test_validation_elliptical_elements_periapsis_apoapsis_and_period(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    rp = 7_000_000.0
    a = 8_000_000.0
    speed = math.sqrt(mu * (2.0 / rp - 1.0 / a))
    initial = np.array([rp, 0, 0, 0, speed, 0], dtype=np.float64)
    energy = ns["orbital_energy"](initial, mu)
    angular_momentum = ns["angular_momentum_magnitude"](initial)
    derived_a = -mu / (2.0 * energy)
    eccentricity = math.sqrt(max(0.0, 1.0 + 2.0 * energy * angular_momentum**2 / mu**2))
    ra = derived_a * (1.0 + eccentricity)
    period = 2.0 * math.pi * math.sqrt(derived_a**3 / mu)

    times, states, collision = ns["propagate"](initial, period, 10.0)
    radii = np.linalg.norm(states[:, :3], axis=1)
    speeds = np.linalg.norm(states[:, 3:], axis=1)
    numerical_rp = float(np.min(radii))
    numerical_ra = float(np.max(radii))
    periapsis_index = int(np.argmin(radii))
    apoapsis_index = int(np.argmax(radii))

    assert collision is None
    assert math.isclose(derived_a, a, rel_tol=1e-12)
    assert math.isclose(rp, derived_a * (1.0 - eccentricity), rel_tol=1e-12)
    assert math.isclose(numerical_rp, rp, rel_tol=2e-7)
    assert math.isclose(numerical_ra, ra, rel_tol=2e-7)
    assert 0.0 < eccentricity < 1.0
    assert math.isclose(times[-1], period, rel_tol=1e-12)

    analytical_apoapsis_speed = math.sqrt(mu * (2.0 / ra - 1.0 / a))
    assert math.isclose(speeds[apoapsis_index], analytical_apoapsis_speed, rel_tol=2e-5)
    assert math.isclose(speeds[periapsis_index], speed, rel_tol=2e-7)
    assert math.isclose(ns["orbital_energy"](states[apoapsis_index], mu), energy, rel_tol=2e-6)
    assert math.isclose(ns["angular_momentum_magnitude"](states[apoapsis_index]), angular_momentum, rel_tol=2e-6)


@pytest.mark.parametrize("duration_fraction", [0.5, 1.0, 2.0])
@pytest.mark.parametrize("dt", [60.0, 30.0, 15.0])
def test_validation_elliptical_conservation_across_timesteps_and_durations(notebook_namespaces, duration_fraction, dt):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    rp = 7_000_000.0
    a = 8_000_000.0
    speed = math.sqrt(mu * (2.0 / rp - 1.0 / a))
    initial = np.array([rp, 0, 0, 0, speed, 0], dtype=np.float64)
    period = 2.0 * math.pi * math.sqrt(a**3 / mu)
    _, states, collision = ns["propagate"](initial, duration_fraction * period, dt)
    assert collision is None

    energies = np.asarray([ns["orbital_energy"](state, mu) for state in states])
    angular_momenta = np.asarray([ns["angular_momentum_magnitude"](state) for state in states])
    energy_absolute = float(np.max(np.abs(energies - energies[0])))
    angular_absolute = float(np.max(np.abs(angular_momenta - angular_momenta[0])))
    relative_energy = energy_absolute / abs(energies[0])
    relative_angular = angular_absolute / angular_momenta[0]

    if duration_fraction <= 1.0:
        assert relative_energy < 5e-3
        assert relative_angular < 5e-5
    else:
        assert relative_energy < 2e-2
        assert relative_angular < 2e-4


def test_validation_elliptical_timestep_sensitivity_converges(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    mu = ns["MU"]
    rp = 7_000_000.0
    a = 8_000_000.0
    speed = math.sqrt(mu * (2.0 / rp - 1.0 / a))
    initial = np.array([rp, 0, 0, 0, speed, 0], dtype=np.float64)
    period = 2.0 * math.pi * math.sqrt(a**3 / mu)
    errors = {}
    for dt in (60.0, 30.0, 15.0):
        _, states, collision = ns["propagate"](initial, period, dt)
        assert collision is None
        errors[dt] = float(np.linalg.norm(states[-1, :3] - initial[:3]))
    assert errors[60.0] > errors[30.0] > errors[15.0]
    ratios = [errors[60.0] / errors[30.0], errors[30.0] / errors[15.0]]
    assert all(12.0 < ratio < 64.0 for ratio in ratios)


def test_validation_collision_and_singular_state(notebook_namespaces):
    ns = notebook_namespaces[NOTEBOOK_NAMES[6]]
    collision_radius = 6_378_137.0
    initial = np.array([collision_radius, 0, 0, 0, 0, 0], dtype=np.float64)
    _, _, collision_index = ns["propagate"](
        initial, 100.0, 1.0, collision_radius=collision_radius
    )
    assert collision_index == 0
    with pytest.raises(ValueError):
        ns["strict_derivative"](
            0.0,
            np.array([0.0, 0, 0, 0, 0, 0]),
            ns["MU"],
        )
