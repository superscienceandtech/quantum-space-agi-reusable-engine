import math
import warnings
from pathlib import Path

import nbformat
import numpy as np
import pytest
from pydantic import ValidationError

from quantum_space_agi.simulation import (
    OrbitalState,
    SimulationConfig,
    diagnose_trajectory,
    eccentricity_vector,
    interpolate_collision_event,
    propagate_two_body,
    rk4_step,
    run_simulation,
    specific_angular_momentum,
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


def circular_orbit_reference(radius_m, mu_m3_s2, time_s):
    angular_velocity_rad_s = math.sqrt(mu_m3_s2 / radius_m**3)
    angle = angular_velocity_rad_s * time_s
    return np.array(
        [
            radius_m * math.cos(angle),
            radius_m * math.sin(angle),
            0.0,
            -radius_m * angular_velocity_rad_s * math.sin(angle),
            radius_m * angular_velocity_rad_s * math.cos(angle),
            0.0,
        ],
        dtype=np.float64,
    )


def elliptical_orbit_reference(semi_major_axis_m, eccentricity, mu_m3_s2, time_s):
    mean_motion_rad_s = math.sqrt(mu_m3_s2 / semi_major_axis_m**3)
    mean_anomaly_rad = mean_motion_rad_s * time_s
    eccentric_anomaly_rad = mean_anomaly_rad
    for _ in range(20):
        correction = (
            eccentric_anomaly_rad
            - eccentricity * math.sin(eccentric_anomaly_rad)
            - mean_anomaly_rad
        ) / (1.0 - eccentricity * math.cos(eccentric_anomaly_rad))
        eccentric_anomaly_rad -= correction
        if abs(correction) < 1e-14:
            break

    denominator = 1.0 - eccentricity * math.cos(eccentric_anomaly_rad)
    minor_axis_factor = math.sqrt(1.0 - eccentricity**2)
    return np.array(
        [
            semi_major_axis_m * (math.cos(eccentric_anomaly_rad) - eccentricity),
            semi_major_axis_m * minor_axis_factor * math.sin(eccentric_anomaly_rad),
            0.0,
            -semi_major_axis_m
            * mean_motion_rad_s
            * math.sin(eccentric_anomaly_rad)
            / denominator,
            semi_major_axis_m
            * mean_motion_rad_s
            * minor_axis_factor
            * math.cos(eccentric_anomaly_rad)
            / denominator,
            0.0,
        ],
        dtype=np.float64,
    )


def perifocal_to_inertial_rotation(ascending_node_rad, inclination_rad, periapsis_rad):
    cos_ascending_node = math.cos(ascending_node_rad)
    sin_ascending_node = math.sin(ascending_node_rad)
    cos_inclination = math.cos(inclination_rad)
    sin_inclination = math.sin(inclination_rad)
    cos_periapsis = math.cos(periapsis_rad)
    sin_periapsis = math.sin(periapsis_rad)
    rotate_ascending_node = np.array(
        [
            [cos_ascending_node, -sin_ascending_node, 0.0],
            [sin_ascending_node, cos_ascending_node, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    rotate_inclination = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, cos_inclination, -sin_inclination],
            [0.0, sin_inclination, cos_inclination],
        ],
        dtype=np.float64,
    )
    rotate_periapsis = np.array(
        [
            [cos_periapsis, -sin_periapsis, 0.0],
            [sin_periapsis, cos_periapsis, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    return rotate_ascending_node @ rotate_inclination @ rotate_periapsis


def radial_fall_time_from_rest(initial_radius_m, target_radius_m, mu_m3_s2):
    radius_ratio = target_radius_m / initial_radius_m
    return math.sqrt(initial_radius_m**3 / (2.0 * mu_m3_s2)) * (
        math.acos(math.sqrt(radius_ratio))
        + math.sqrt(radius_ratio * (1.0 - radius_ratio))
    )


def long_term_elliptical_metrics(periods, steps_per_orbit):
    semi_major_axis_m = 10_000_000.0
    eccentricity = 0.25
    mu_m3_s2 = EARTH_MU_M3_S2
    rotation = perifocal_to_inertial_rotation(
        *map(math.radians, (40.0, 55.0, 30.0))
    )
    periapsis_m = semi_major_axis_m * (1.0 - eccentricity)
    periapsis_speed_mps = math.sqrt(
        mu_m3_s2
        * (1.0 + eccentricity)
        / (semi_major_axis_m * (1.0 - eccentricity))
    )
    initial_position_m = rotation @ np.array([periapsis_m, 0.0, 0.0])
    initial_velocity_mps = rotation @ np.array([0.0, periapsis_speed_mps, 0.0])
    period_s = 2.0 * math.pi * math.sqrt(semi_major_axis_m**3 / mu_m3_s2)
    result = run_simulation(
        example_config(
            initial_position_m=tuple(initial_position_m),
            initial_velocity_mps=tuple(initial_velocity_mps),
            simulation_duration_s=periods * period_s,
            time_step_s=period_s / steps_per_orbit,
        )
    )

    sample_indices = {
        round((orbit + phase) * steps_per_orbit)
        for orbit in range(periods)
        for phase in (0.0, 0.25, 0.5, 0.75, 1.0)
    }
    position_errors_m = []
    velocity_errors_mps = []
    for sample_index in sorted(sample_indices):
        perifocal_reference = elliptical_orbit_reference(
            semi_major_axis_m,
            eccentricity,
            mu_m3_s2,
            result["times_s"][sample_index],
        )
        expected = np.concatenate(
            (
                rotation @ perifocal_reference[:3],
                rotation @ perifocal_reference[3:],
            )
        )
        error = result["states"][sample_index] - expected
        position_errors_m.append(float(np.linalg.norm(error[:3])))
        velocity_errors_mps.append(float(np.linalg.norm(error[3:])))

    expected_angular_momentum = rotation @ np.array(
        [
            0.0,
            0.0,
            math.sqrt(
                mu_m3_s2
                * semi_major_axis_m
                * (1.0 - eccentricity**2)
            ),
        ]
    )
    expected_eccentricity = rotation @ np.array([eccentricity, 0.0, 0.0])
    angular_momentum_vector_errors = []
    angular_momentum_direction_errors_rad = []
    eccentricity_magnitude_errors = []
    eccentricity_vector_errors = []
    eccentricity_direction_errors_rad = []
    for state in result["states"]:
        angular_momentum = np.cross(state[:3], state[3:])
        state_eccentricity, state_eccentricity_magnitude = eccentricity_vector(
            state,
            mu_m3_s2,
        )
        angular_momentum_vector_errors.append(
            float(np.linalg.norm(angular_momentum - expected_angular_momentum))
        )
        angular_momentum_direction_errors_rad.append(
            math.atan2(
                np.linalg.norm(
                    np.cross(angular_momentum, expected_angular_momentum)
                ),
                float(np.dot(angular_momentum, expected_angular_momentum)),
            )
        )
        eccentricity_magnitude_errors.append(
            abs(state_eccentricity_magnitude - eccentricity)
        )
        eccentricity_vector_errors.append(
            float(np.linalg.norm(state_eccentricity - expected_eccentricity))
        )
        eccentricity_direction_errors_rad.append(
            math.atan2(
                np.linalg.norm(
                    np.cross(state_eccentricity, expected_eccentricity)
                ),
                float(np.dot(state_eccentricity, expected_eccentricity)),
            )
        )

    diagnostics = result["diagnostics"]
    initial_energy = abs(float(diagnostics["specific_energy_m2_s2"][0]))
    initial_angular_momentum = float(
        diagnostics["specific_angular_momentum_m2_s"][0]
    )
    expected_angular_momentum_magnitude = float(
        np.linalg.norm(expected_angular_momentum)
    )
    return {
        "collision_index": result["collision_index"],
        "max_position_error_m": max(position_errors_m),
        "max_velocity_error_mps": max(velocity_errors_mps),
        "relative_energy_drift": (
            diagnostics["max_abs_energy_drift_m2_s2"] / initial_energy
        ),
        "relative_angular_momentum_drift": (
            diagnostics["max_abs_angular_momentum_drift_m2_s"]
            / initial_angular_momentum
        ),
        "relative_angular_momentum_vector_error": (
            max(angular_momentum_vector_errors)
            / expected_angular_momentum_magnitude
        ),
        "angular_momentum_direction_error_rad": max(
            angular_momentum_direction_errors_rad
        ),
        "eccentricity_magnitude_error": max(eccentricity_magnitude_errors),
        "eccentricity_vector_error": max(eccentricity_vector_errors),
        "eccentricity_direction_error_rad": max(
            eccentricity_direction_errors_rad
        ),
    }


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


def test_package_circular_orbit_matches_analytical_states_and_invariants():
    radius_m = 7_000_000.0
    mu_m3_s2 = EARTH_MU_M3_S2
    angular_velocity_rad_s = math.sqrt(mu_m3_s2 / radius_m**3)
    period_s = 2.0 * math.pi / angular_velocity_rad_s
    time_step_s = period_s / 64.0
    config = example_config(
        initial_position_m=(radius_m, 0.0, 0.0),
        initial_velocity_mps=(0.0, math.sqrt(mu_m3_s2 / radius_m), 0.0),
        simulation_duration_s=period_s,
        time_step_s=time_step_s,
    )

    result = run_simulation(config)

    assert result["collision_index"] is None
    for sample_index in (0, 16, 32, 48, 64):
        sample_time_s = sample_index * time_step_s
        assert result["times_s"][sample_index] == pytest.approx(sample_time_s, abs=1e-9)
        actual = result["states"][sample_index]
        expected = circular_orbit_reference(
            radius_m,
            mu_m3_s2,
            sample_time_s,
        )
        # With 64 steps per orbit, the angular step is below 0.1 rad; these
        # bounds allow the observed global RK4 phase error over one full orbit.
        assert np.linalg.norm(actual[:3] - expected[:3]) < 250.0
        assert np.linalg.norm(actual[3:] - expected[3:]) < 0.25

    diagnostics = result["diagnostics"]
    initial_energy = abs(diagnostics["specific_energy_m2_s2"][0])
    initial_angular_momentum = diagnostics["specific_angular_momentum_m2_s"][0]
    assert diagnostics["max_abs_energy_drift_m2_s2"] / initial_energy < 1e-5
    assert (
        diagnostics["max_abs_angular_momentum_drift_m2_s"]
        / initial_angular_momentum
        < 1e-5
    )


def test_package_circular_orbit_error_decreases_with_rk4_timestep_refinement():
    radius_m = 7_000_000.0
    mu_m3_s2 = EARTH_MU_M3_S2
    angular_velocity_rad_s = math.sqrt(mu_m3_s2 / radius_m**3)
    period_s = 2.0 * math.pi / angular_velocity_rad_s
    initial_position = np.array([radius_m, 0.0, 0.0], dtype=np.float64)
    initial_velocity = np.array(
        [0.0, math.sqrt(mu_m3_s2 / radius_m), 0.0],
        dtype=np.float64,
    )
    errors_m = []

    for steps_per_orbit in (20, 40, 80):
        result = run_simulation(
            example_config(
                initial_position_m=tuple(initial_position),
                initial_velocity_mps=tuple(initial_velocity),
                simulation_duration_s=period_s,
                time_step_s=period_s / steps_per_orbit,
            )
        )
        errors_m.append(float(np.linalg.norm(result["states"][-1, :3] - initial_position)))

    assert errors_m[0] > errors_m[1] > errors_m[2]
    # RK4's global error is O(dt^4); allow a broad ratio range to avoid relying
    # on exact asymptotic constants for this nonlinear orbital problem.
    ratios = [coarse / fine for coarse, fine in zip(errors_m, errors_m[1:])]
    assert all(8.0 < ratio < 32.0 for ratio in ratios)


def test_package_elliptical_orbit_matches_kepler_reference_and_conserves_invariants():
    semi_major_axis_m = 10_000_000.0
    eccentricity = 0.25
    mu_m3_s2 = EARTH_MU_M3_S2
    periapsis_m = semi_major_axis_m * (1.0 - eccentricity)
    periapsis_speed_mps = math.sqrt(
        mu_m3_s2
        * (1.0 + eccentricity)
        / (semi_major_axis_m * (1.0 - eccentricity))
    )
    mean_motion_rad_s = math.sqrt(mu_m3_s2 / semi_major_axis_m**3)
    period_s = 2.0 * math.pi / mean_motion_rad_s
    steps_per_orbit = 128
    config = example_config(
        initial_position_m=(periapsis_m, 0.0, 0.0),
        initial_velocity_mps=(0.0, periapsis_speed_mps, 0.0),
        simulation_duration_s=period_s,
        time_step_s=period_s / steps_per_orbit,
    )

    result = run_simulation(config)

    assert result["collision_index"] is None
    position_errors_m = []
    velocity_errors_mps = []
    for sample_index in (0, 16, 32, 64, 96, 112, 128):
        actual = result["states"][sample_index]
        expected = elliptical_orbit_reference(
            semi_major_axis_m,
            eccentricity,
            mu_m3_s2,
            result["times_s"][sample_index],
        )
        position_errors_m.append(float(np.linalg.norm(actual[:3] - expected[:3])))
        velocity_errors_mps.append(float(np.linalg.norm(actual[3:] - expected[3:])))

    # At 128 RK4 steps/orbit the measured maxima were 50.18 m and 0.04814 m/s;
    # these bounds leave modest margin while staying tied to the measured error.
    assert max(position_errors_m) < 55.0
    assert max(velocity_errors_mps) < 0.052

    diagnostics = result["diagnostics"]
    initial_energy = abs(float(diagnostics["specific_energy_m2_s2"][0]))
    initial_angular_momentum = float(
        diagnostics["specific_angular_momentum_m2_s"][0]
    )
    assert (
        diagnostics["max_abs_energy_drift_m2_s2"] / initial_energy
        < 5e-7
    )
    assert (
        diagnostics["max_abs_angular_momentum_drift_m2_s"]
        / initial_angular_momentum
        < 1e-7
    )

    expected_eccentricity_vector = np.array([eccentricity, 0.0, 0.0])
    eccentricity_errors = [
        np.linalg.norm(
            eccentricity_vector(state, mu_m3_s2)[0]
            - expected_eccentricity_vector
        )
        for state in result["states"]
    ]
    assert max(eccentricity_errors) < 1.25e-6


def test_package_elliptical_orbit_error_decreases_with_rk4_timestep_refinement():
    semi_major_axis_m = 10_000_000.0
    eccentricity = 0.25
    mu_m3_s2 = EARTH_MU_M3_S2
    periapsis_m = semi_major_axis_m * (1.0 - eccentricity)
    periapsis_speed_mps = math.sqrt(
        mu_m3_s2
        * (1.0 + eccentricity)
        / (semi_major_axis_m * (1.0 - eccentricity))
    )
    period_s = 2.0 * math.pi * math.sqrt(semi_major_axis_m**3 / mu_m3_s2)
    position_errors_m = []
    velocity_errors_mps = []

    for steps_per_orbit in (32, 64, 128):
        result = run_simulation(
            example_config(
                initial_position_m=(periapsis_m, 0.0, 0.0),
                initial_velocity_mps=(0.0, periapsis_speed_mps, 0.0),
                simulation_duration_s=period_s,
                time_step_s=period_s / steps_per_orbit,
            )
        )
        sample_errors = [
            result["states"][round(steps_per_orbit * fraction)]
            - elliptical_orbit_reference(
                semi_major_axis_m,
                eccentricity,
                mu_m3_s2,
                result["times_s"][round(steps_per_orbit * fraction)],
            )
            for fraction in (0.0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0)
        ]
        position_errors_m.append(
            max(float(np.linalg.norm(error[:3])) for error in sample_errors)
        )
        velocity_errors_mps.append(
            max(float(np.linalg.norm(error[3:])) for error in sample_errors)
        )

    assert position_errors_m[0] > position_errors_m[1] > position_errors_m[2]
    assert velocity_errors_mps[0] > velocity_errors_mps[1] > velocity_errors_mps[2]
    # Halving dt should approach the RK4 global-error ratio of 16. Measured
    # position ratios were 24.4 and 20.5; velocity ratios were 23.6 and 20.7.
    position_ratios = [
        coarse / fine
        for coarse, fine in zip(position_errors_m, position_errors_m[1:])
    ]
    velocity_ratios = [
        coarse / fine
        for coarse, fine in zip(velocity_errors_mps, velocity_errors_mps[1:])
    ]
    assert all(10.0 < ratio < 40.0 for ratio in position_ratios)
    assert all(10.0 < ratio < 40.0 for ratio in velocity_ratios)


def test_package_3d_elliptical_orbit_matches_rotated_kepler_reference_and_invariants():
    semi_major_axis_m = 10_000_000.0
    eccentricity = 0.25
    mu_m3_s2 = EARTH_MU_M3_S2
    ascending_node_rad, inclination_rad, periapsis_rad = map(
        math.radians,
        (40.0, 55.0, 30.0),
    )
    rotation = perifocal_to_inertial_rotation(
        ascending_node_rad,
        inclination_rad,
        periapsis_rad,
    )
    periapsis_m = semi_major_axis_m * (1.0 - eccentricity)
    periapsis_speed_mps = math.sqrt(
        mu_m3_s2
        * (1.0 + eccentricity)
        / (semi_major_axis_m * (1.0 - eccentricity))
    )
    initial_position_m = rotation @ np.array([periapsis_m, 0.0, 0.0])
    initial_velocity_mps = rotation @ np.array([0.0, periapsis_speed_mps, 0.0])
    period_s = 2.0 * math.pi * math.sqrt(semi_major_axis_m**3 / mu_m3_s2)
    steps_per_orbit = 128
    result = run_simulation(
        example_config(
            initial_position_m=tuple(initial_position_m),
            initial_velocity_mps=tuple(initial_velocity_mps),
            simulation_duration_s=period_s,
            time_step_s=period_s / steps_per_orbit,
        )
    )

    assert result["collision_index"] is None
    assert np.count_nonzero(initial_position_m) == 3
    assert np.count_nonzero(initial_velocity_mps) == 3
    position_errors_m = []
    velocity_errors_mps = []
    for sample_index in (0, 16, 32, 64, 96, 112, 128):
        perifocal_reference = elliptical_orbit_reference(
            semi_major_axis_m,
            eccentricity,
            mu_m3_s2,
            result["times_s"][sample_index],
        )
        expected = np.concatenate(
            (
                rotation @ perifocal_reference[:3],
                rotation @ perifocal_reference[3:],
            )
        )
        actual = result["states"][sample_index]
        position_errors_m.append(float(np.linalg.norm(actual[:3] - expected[:3])))
        velocity_errors_mps.append(float(np.linalg.norm(actual[3:] - expected[3:])))

    # The measured 128-step maxima are 50.18 m and 0.04814 m/s, matching the
    # planar case under rotation; bounds leave modest margin without widening it.
    assert max(position_errors_m) < 55.0
    assert max(velocity_errors_mps) < 0.052

    diagnostics = result["diagnostics"]
    initial_energy = abs(float(diagnostics["specific_energy_m2_s2"][0]))
    initial_angular_momentum = float(
        diagnostics["specific_angular_momentum_m2_s"][0]
    )
    assert (
        diagnostics["max_abs_energy_drift_m2_s2"] / initial_energy
        < 5e-7
    )
    assert (
        diagnostics["max_abs_angular_momentum_drift_m2_s"]
        / initial_angular_momentum
        < 1e-7
    )

    expected_angular_momentum = rotation @ np.array(
        [
            0.0,
            0.0,
            math.sqrt(mu_m3_s2 * semi_major_axis_m * (1.0 - eccentricity**2)),
        ]
    )
    expected_eccentricity = rotation @ np.array([eccentricity, 0.0, 0.0])
    angular_momentum_vector_errors = []
    eccentricity_vector_errors = []
    angular_momentum_direction_errors_rad = []
    eccentricity_direction_errors_rad = []
    eccentricity_magnitude_errors = []
    for state in result["states"]:
        angular_momentum = np.cross(state[:3], state[3:])
        state_eccentricity_vector, eccentricity_magnitude = eccentricity_vector(
            state,
            mu_m3_s2,
        )
        angular_momentum_vector_errors.append(
            float(np.linalg.norm(angular_momentum - expected_angular_momentum))
        )
        eccentricity_vector_errors.append(
            float(np.linalg.norm(state_eccentricity_vector - expected_eccentricity))
        )
        eccentricity_magnitude_errors.append(
            abs(eccentricity_magnitude - eccentricity)
        )
        angular_momentum_direction_errors_rad.append(
            math.atan2(
                np.linalg.norm(
                    np.cross(angular_momentum, expected_angular_momentum)
                ),
                float(np.dot(angular_momentum, expected_angular_momentum)),
            )
        )
        eccentricity_direction_errors_rad.append(
            math.atan2(
                np.linalg.norm(
                    np.cross(state_eccentricity_vector, expected_eccentricity)
                ),
                float(np.dot(state_eccentricity_vector, expected_eccentricity)),
            )
        )

    expected_angular_momentum_magnitude = float(np.linalg.norm(expected_angular_momentum))
    assert (
        max(angular_momentum_vector_errors) / expected_angular_momentum_magnitude
        < 1e-7
    )
    assert max(angular_momentum_direction_errors_rad) < 1e-12
    assert max(eccentricity_magnitude_errors) < 1.25e-6
    assert max(eccentricity_vector_errors) < 1.25e-6
    assert max(eccentricity_direction_errors_rad) < 4.5e-6


def test_package_3d_elliptical_orbit_error_decreases_with_rk4_timestep_refinement():
    semi_major_axis_m = 10_000_000.0
    eccentricity = 0.25
    mu_m3_s2 = EARTH_MU_M3_S2
    rotation = perifocal_to_inertial_rotation(
        *map(math.radians, (40.0, 55.0, 30.0))
    )
    periapsis_m = semi_major_axis_m * (1.0 - eccentricity)
    periapsis_speed_mps = math.sqrt(
        mu_m3_s2
        * (1.0 + eccentricity)
        / (semi_major_axis_m * (1.0 - eccentricity))
    )
    initial_position_m = rotation @ np.array([periapsis_m, 0.0, 0.0])
    initial_velocity_mps = rotation @ np.array([0.0, periapsis_speed_mps, 0.0])
    period_s = 2.0 * math.pi * math.sqrt(semi_major_axis_m**3 / mu_m3_s2)
    position_errors_m = []
    velocity_errors_mps = []

    for steps_per_orbit in (32, 64, 128):
        result = run_simulation(
            example_config(
                initial_position_m=tuple(initial_position_m),
                initial_velocity_mps=tuple(initial_velocity_mps),
                simulation_duration_s=period_s,
                time_step_s=period_s / steps_per_orbit,
            )
        )
        sample_errors = []
        for fraction in (0.0, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0):
            sample_index = round(steps_per_orbit * fraction)
            perifocal_reference = elliptical_orbit_reference(
                semi_major_axis_m,
                eccentricity,
                mu_m3_s2,
                result["times_s"][sample_index],
            )
            expected = np.concatenate(
                (
                    rotation @ perifocal_reference[:3],
                    rotation @ perifocal_reference[3:],
                )
            )
            sample_errors.append(result["states"][sample_index] - expected)

        position_errors_m.append(
            max(float(np.linalg.norm(error[:3])) for error in sample_errors)
        )
        velocity_errors_mps.append(
            max(float(np.linalg.norm(error[3:])) for error in sample_errors)
        )

    assert position_errors_m[0] > position_errors_m[1] > position_errors_m[2]
    assert velocity_errors_mps[0] > velocity_errors_mps[1] > velocity_errors_mps[2]
    position_ratios = [
        coarse / fine
        for coarse, fine in zip(position_errors_m, position_errors_m[1:])
    ]
    velocity_ratios = [
        coarse / fine
        for coarse, fine in zip(velocity_errors_mps, velocity_errors_mps[1:])
    ]
    assert all(10.0 < ratio < 40.0 for ratio in position_ratios)
    assert all(10.0 < ratio < 40.0 for ratio in velocity_ratios)


@pytest.mark.parametrize(
    (
        "periods",
        "position_limit_m",
        "velocity_limit_mps",
        "energy_drift_limit",
        "angular_momentum_drift_limit",
        "eccentricity_magnitude_limit",
        "eccentricity_vector_limit",
        "eccentricity_direction_limit_rad",
    ),
    [
        (10, 2_000.0, 1.8, 3e-6, 1e-6, 2.3e-6, 1.2e-5, 4.5e-5),
        (50, 42_000.0, 36.0, 1.35e-5, 4.1e-6, 9.5e-6, 5.7e-5, 2.3e-4),
    ],
)
def test_package_elliptical_orbit_long_term_stability_and_invariant_drift(
    periods,
    position_limit_m,
    velocity_limit_mps,
    energy_drift_limit,
    angular_momentum_drift_limit,
    eccentricity_magnitude_limit,
    eccentricity_vector_limit,
    eccentricity_direction_limit_rad,
):
    # Limits are based on measured 128-step/orbit errors at these durations.
    metrics = long_term_elliptical_metrics(periods, steps_per_orbit=128)

    assert metrics["collision_index"] is None
    assert metrics["max_position_error_m"] < position_limit_m
    assert metrics["max_velocity_error_mps"] < velocity_limit_mps
    assert metrics["relative_energy_drift"] < energy_drift_limit
    assert (
        metrics["relative_angular_momentum_drift"]
        < angular_momentum_drift_limit
    )
    assert (
        metrics["relative_angular_momentum_vector_error"]
        < angular_momentum_drift_limit
    )
    assert metrics["angular_momentum_direction_error_rad"] < 1e-12
    assert (
        metrics["eccentricity_magnitude_error"]
        < eccentricity_magnitude_limit
    )
    assert metrics["eccentricity_vector_error"] < eccentricity_vector_limit
    assert (
        metrics["eccentricity_direction_error_rad"]
        < eccentricity_direction_limit_rad
    )


def test_package_elliptical_orbit_long_term_errors_decrease_with_timestep_refinement():
    # Fifty-orbit maxima are compared at common orbital phases; RK4's state and
    # invariant errors improve with refinement, but need not share one ratio.
    coarse = long_term_elliptical_metrics(periods=50, steps_per_orbit=64)
    fine = long_term_elliptical_metrics(periods=50, steps_per_orbit=128)

    assert coarse["collision_index"] is None
    assert fine["collision_index"] is None
    for metric in (
        "max_position_error_m",
        "max_velocity_error_mps",
        "relative_energy_drift",
        "relative_angular_momentum_drift",
        "relative_angular_momentum_vector_error",
        "eccentricity_magnitude_error",
        "eccentricity_vector_error",
        "eccentricity_direction_error_rad",
    ):
        assert coarse[metric] > fine[metric], metric
    assert fine["angular_momentum_direction_error_rad"] < 1e-12
    assert coarse["angular_momentum_direction_error_rad"] < 1e-12


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


def test_rk4_derivative_mutation_does_not_change_integrator_state():
    state = np.array([1.0], dtype=np.float64)

    def mutating_derivative(_time, derivative_state):
        derivative_state[0] = 99.0
        return np.array([0.0], dtype=np.float64)

    result = rk4_step(state, 0.0, 0.1, mutating_derivative)

    assert state.tolist() == [1.0]
    assert result.tolist() == [1.0]


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


def test_collision_interpolation_rejects_equal_endpoint_times():
    previous = np.array([6_400_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0], dtype=np.float64)
    following = np.array([6_300_000.0, 0.0, 0.0, 0.0, 7_400.0, 0.0], dtype=np.float64)
    with pytest.raises(ValueError, match="strictly increasing"):
        interpolate_collision_event(
            5.0,
            previous,
            5.0,
            following,
            6_378_137.0,
        )


def test_collision_free_trajectory_reports_no_event():
    result = run_simulation(
        example_config(
            simulation_duration_s=600.0,
            collision_radius_m=EARTH_REFERENCE_RADIUS_M,
        )
    )

    assert np.all(
        result["diagnostics"]["radius_m"] > EARTH_REFERENCE_RADIUS_M
    )
    assert result["collision_index"] is None
    assert result["collision_time_s"] is None
    assert result["collision_state"] is None


def test_initial_state_exactly_on_collision_boundary_is_reported_at_zero():
    result = propagate_two_body(
        np.array(
            [EARTH_REFERENCE_RADIUS_M, 0.0, 0.0, 0.0, 0.0, 0.0],
            dtype=np.float64,
        ),
        EARTH_MU_M3_S2,
        600.0,
        10.0,
        EARTH_REFERENCE_RADIUS_M,
    )

    assert result["collision_index"] == 0
    assert result["collision_time_s"] == 0.0
    assert result["collision_method"] == "exact_sample"
    assert np.array_equal(result["collision_state"], result["states"][0])


def test_collision_interpolation_exact_sample_endpoint_is_not_approximated():
    previous = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_000.0, 0.0])
    boundary = np.array(
        [EARTH_REFERENCE_RADIUS_M, 0.0, 0.0, 0.0, 7_500.0, 0.0],
        dtype=np.float64,
    )

    event_time, event_state, method = interpolate_collision_event(
        10.0,
        previous,
        20.0,
        boundary,
        EARTH_REFERENCE_RADIUS_M,
    )

    assert event_time == 20.0
    assert method == "exact_sample"
    assert np.array_equal(event_state, boundary)


def test_collision_interpolation_matches_independent_radial_linear_calculation():
    previous = np.array([7_000_000.0, 0.0, 0.0, 0.0, 7_000.0, 0.0])
    following = np.array([6_000_000.0, 0.0, 0.0, 0.0, 6_000.0, 0.0])
    previous_time_s = 12.0
    next_time_s = 32.0
    collision_radius_m = 6_400_000.0
    alpha = (collision_radius_m - 7_000_000.0) / (6_000_000.0 - 7_000_000.0)
    expected_time_s = previous_time_s + alpha * (next_time_s - previous_time_s)
    expected_state = (1.0 - alpha) * previous + alpha * following

    event_time_s, event_state, method = interpolate_collision_event(
        previous_time_s,
        previous,
        next_time_s,
        following,
        collision_radius_m,
    )

    assert method == "linear_radius_interpolation"
    assert event_time_s == pytest.approx(expected_time_s, abs=1e-12)
    assert np.array_equal(event_state, expected_state)


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_collision_interpolation_keeps_finite_time_for_extreme_finite_bracket(
    numpy_error_policy,
):
    previous = np.array([7_000_000.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    following = np.array([6_000_000.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    with np.errstate(all=numpy_error_policy):
        event_time, event_state, method = interpolate_collision_event(
            -1e308,
            previous,
            1e308,
            following,
            6_500_000.0,
        )

    assert math.isfinite(event_time)
    assert event_time == 0.0
    assert method == "linear_radius_interpolation"
    assert event_state[0] == 6_500_000.0


def test_collision_between_samples_matches_independent_radial_fall_reference_and_refines():
    initial_radius_m = 7_000_000.0
    collision_radius_m = EARTH_REFERENCE_RADIUS_M
    mu_m3_s2 = EARTH_MU_M3_S2
    exact_collision_time_s = radial_fall_time_from_rest(
        initial_radius_m,
        collision_radius_m,
        mu_m3_s2,
    )
    event_time_errors_s = []

    for time_step_s, max_time_error_s in ((120.0, 3.5), (30.0, 0.25)):
        result = run_simulation(
            example_config(
                initial_position_m=(initial_radius_m, 0.0, 0.0),
                initial_velocity_mps=(0.0, 0.0, 0.0),
                simulation_duration_s=exact_collision_time_s + 2.0 * time_step_s,
                time_step_s=time_step_s,
                collision_radius_m=collision_radius_m,
            )
        )

        assert result["collision_index"] is not None
        assert (
            result["times_s"][result["collision_index"]] > exact_collision_time_s
        )
        assert result["collision_method"] == "linear_radius_interpolation"
        assert result["collision_time_s"] < result["times_s"][result["collision_index"]]
        assert result["collision_time_s"] == pytest.approx(
            exact_collision_time_s,
            abs=max_time_error_s,
        )
        assert result["collision_state"][:3] == pytest.approx(
            [collision_radius_m, 0.0, 0.0],
            abs=1e-8,
        )
        assert np.linalg.norm(result["collision_state"][:3]) == pytest.approx(
            collision_radius_m,
            abs=1e-8,
        )
        event_time_errors_s.append(
            abs(result["collision_time_s"] - exact_collision_time_s)
        )

    assert event_time_errors_s[1] < event_time_errors_s[0]


def test_approaching_but_not_yet_crossing_collision_boundary_reports_no_event():
    initial_radius_m = 7_000_000.0
    collision_radius_m = EARTH_REFERENCE_RADIUS_M
    result = run_simulation(
        example_config(
            initial_position_m=(initial_radius_m, 0.0, 0.0),
            initial_velocity_mps=(0.0, 0.0, 0.0),
            simulation_duration_s=360.0,
            time_step_s=10.0,
            collision_radius_m=collision_radius_m,
        )
    )

    assert result["diagnostics"]["radius_m"][-1] > collision_radius_m
    assert result["collision_index"] is None
    assert result["collision_time_s"] is None
    assert result["collision_state"] is None


def test_collision_detection_recognizes_initial_state_on_boundary_for_inward_motion():
    initial = np.array(
        [EARTH_REFERENCE_RADIUS_M, 0.0, 0.0, -1_000.0, 0.0, 0.0],
        dtype=np.float64,
    )
    result = propagate_two_body(
        initial,
        EARTH_MU_M3_S2,
        5.0,
        0.5,
        EARTH_REFERENCE_RADIUS_M,
    )

    assert result["collision_index"] == 0
    assert result["collision_time_s"] == 0.0
    assert result["collision_method"] == "exact_sample"
    assert np.allclose(result["collision_state"][:3], initial[:3], atol=1e-12)


def test_collision_interpolation_rejects_decreasing_endpoint_times():
    previous = np.array([6_400_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0])
    following = np.array([6_300_000.0, 0.0, 0.0, 0.0, 7_400.0, 0.0])

    with pytest.raises(ValueError, match="strictly increasing"):
        interpolate_collision_event(
            10.0,
            previous,
            9.0,
            following,
            EARTH_REFERENCE_RADIUS_M,
        )


@pytest.mark.parametrize(
    ("previous_time_s", "previous_state", "next_time_s", "next_state", "threshold"),
    [
        (
            0.0,
            [7e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            float("nan"),
            [6e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            6.5e6,
        ),
        (
            0.0,
            [7e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            1.0,
            [float("inf"), 0.0, 0.0, 0.0, 0.0, 0.0],
            6.5e6,
        ),
        (
            0.0,
            [7e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            1.0,
            [6e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            float("inf"),
        ),
        (
            0.0,
            [7e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            1.0,
            [6e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            0.0,
        ),
    ],
)
def test_collision_interpolation_rejects_nonfinite_inputs(
    previous_time_s,
    previous_state,
    next_time_s,
    next_state,
    threshold,
):
    with pytest.raises(ValueError):
        interpolate_collision_event(
            previous_time_s,
            previous_state,
            next_time_s,
            next_state,
            threshold,
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


@pytest.mark.parametrize(
    ("duration_s", "time_step_s"),
    [(1e-12, 1e-12), (1e-12, 1.0)],
)
def test_short_duration_and_final_partial_step_produce_finite_time_grid(
    duration_s,
    time_step_s,
):
    result = run_simulation(
        example_config(
            simulation_duration_s=duration_s,
            time_step_s=time_step_s,
        )
    )

    assert result["times_s"].tolist() == [0.0, duration_s]
    assert np.all(np.isfinite(result["states"]))


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_timestep_too_small_to_advance_duration_grid_is_rejected(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            with pytest.raises(ValueError, match="too small to represent"):
                run_simulation(
                    example_config(
                        simulation_duration_s=1.0,
                        time_step_s=1e-300,
                    )
                )
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
@pytest.mark.parametrize(
    ("position_m", "message"),
    [
        ((1e-200, 0.0, 0.0), "Acceleration magnitude is non-finite"),
        ((1e308, 0.0, 0.0), "Acceleration magnitude underflows float64"),
    ],
)
def test_gravity_overflow_and_underflow_fail_consistently(
    position_m,
    message,
    numpy_error_policy,
):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            with pytest.raises(ValueError, match=message):
                two_body_derivative(
                    np.array([*position_m, 0.0, 0.0, 0.0]),
                    EARTH_MU_M3_S2,
                )
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_invalid_initial_state_fails_consistently(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            with pytest.raises(ValueError, match="finite six-component vector"):
                propagate_two_body(
                    np.array([float("nan"), 0.0, 0.0, 0.0, 7500.0, 0.0]),
                    EARTH_MU_M3_S2,
                    1.0,
                    0.1,
                    EARTH_REFERENCE_RADIUS_M,
                )
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_invalid_configuration_fails_consistently(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            with pytest.raises(ValidationError):
                example_config(simulation_duration_s=float("nan"))
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_nonfinite_derivative_output_fails_consistently(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            with pytest.raises(ValueError, match="RK4 intermediate stage is invalid"):
                rk4_step(
                    np.array([1.0]),
                    0.0,
                    1.0,
                    lambda _time, state: np.full_like(state, np.inf),
                )
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_extreme_finite_velocity_fails_diagnostics_reproducibly(numpy_error_policy):
    config = example_config(
        initial_velocity_mps=(1e200, 0.0, 0.0),
        simulation_duration_s=1e-200,
        time_step_s=1e-200,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            for _ in range(2):
                with pytest.raises(
                    ValueError,
                    match="Specific orbital energy is non-finite",
                ):
                    run_simulation(config)
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_workflow_does_not_return_trajectory_when_diagnostics_fail(numpy_error_policy):
    config = example_config(
        initial_velocity_mps=(1e200, 0.0, 0.0),
        simulation_duration_s=1e-200,
        time_step_s=1e-200,
    )
    initial_state = OrbitalState(
        position_m=config.initial_position_m,
        velocity_mps=config.initial_velocity_mps,
        time_s=0.0,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            trajectory = propagate_two_body(
                initial_state.to_array(),
                config.gravitational_parameter_m3_s2,
                config.simulation_duration_s,
                config.time_step_s,
                config.collision_radius_m,
            )
            assert np.all(np.isfinite(trajectory["states"]))
            with pytest.raises(ValueError, match="Specific orbital energy is non-finite"):
                diagnose_trajectory(
                    trajectory["times_s"],
                    trajectory["states"],
                    config.gravitational_parameter_m3_s2,
                )
            with pytest.raises(ValueError, match="Specific orbital energy is non-finite"):
                run_simulation(config)
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (
            lambda: diagnose_trajectory(
                np.array([0.0, 1.0]),
                np.array(
                    [
                        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [10.0, 0.0, 0.0, 1.8e154, 0.0, 0.0],
                    ]
                ),
                1e308,
            ),
            "Trajectory diagnostics contain non-finite results",
        ),
        (
            lambda: specific_angular_momentum(
                np.array([1e200, 0.0, 0.0, 0.0, 1e200, 0.0])
            ),
            "Angular momentum contains non-finite values",
        ),
        (
            lambda: eccentricity_vector(
                np.array([1e100, 0.0, 0.0, 0.0, 1e150, 0.0]),
                EARTH_MU_M3_S2,
            ),
            "Eccentricity vector contains non-finite values",
        ),
        (
            lambda: diagnose_trajectory(
                np.array([-1e308, 1e308]),
                np.array(
                    [
                        [7e6, 0.0, 0.0, 0.0, 7500.0, 0.0],
                        [7e6, 0.0, 0.0, 0.0, 7500.0, 0.0],
                    ]
                ),
                EARTH_MU_M3_S2,
            ),
            "Times must have finite differences",
        ),
        (
            lambda: eccentricity_vector(
                np.array([1e-200, 0.0, 0.0, 0.0, 1e-200, 0.0]),
                EARTH_MU_M3_S2,
            ),
            None,
        ),
    ],
)
def test_diagnostic_calculation_is_numpy_policy_independent(
    operation,
    message,
    numpy_error_policy,
):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            if message is None:
                vector, magnitude = operation()
                assert np.all(np.isfinite(vector))
                assert math.isfinite(magnitude)
            else:
                with pytest.raises(ValueError, match=message):
                    operation()
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_nominal_workflow_succeeds_under_numpy_error_policies(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            result = run_simulation(example_config())
    assert np.all(np.isfinite(result["states"]))
    assert not caught


@pytest.mark.parametrize("numpy_error_policy", ["ignore", "warn", "raise"])
def test_rk4_and_gravity_are_numpy_underflow_policy_independent(numpy_error_policy):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(all=numpy_error_policy):
            derivative = two_body_derivative(
                np.array([1e100, 1e-300, 0.0, 0.0, 0.0, 0.0]),
                EARTH_MU_M3_S2,
            )
            result = rk4_step(
                np.array([1.0]),
                0.0,
                1e-200,
                lambda _time, _state: np.array([1e-200]),
            )
    assert np.all(np.isfinite(derivative))
    assert result.tolist() == [1.0]
    assert not caught


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


@pytest.mark.parametrize("overflow_stage", [1, 2, 3])
def test_rk4_rejects_nonfinite_intermediate_state_before_evaluating_it(overflow_stage):
    derivative_calls = 0

    def derivative(_time, state):
        nonlocal derivative_calls
        derivative_calls += 1
        value = 1e308 if derivative_calls == overflow_stage else 0.0
        return np.full_like(state, value)

    with pytest.raises(ValueError, match="RK4 intermediate state is non-finite"):
        rk4_step(
            np.array([1.7e308], dtype=np.float64),
            0.0,
            1.0,
            derivative,
        )
    assert derivative_calls == overflow_stage


def test_rk4_rejects_overflow_in_final_weighted_stage_sum():
    with pytest.raises(ValueError, match="RK4 produced a non-finite state"):
        rk4_step(
            np.array([0.0], dtype=np.float64),
            0.0,
            1.0,
            lambda _time, state: np.full_like(state, 1e308),
        )


@pytest.mark.parametrize(
    "argument,value",
    [
        ("times_s", ["0", "1"]),
        ("times_s", True),
        ("times_s", np.array([False, True])),
        ("times_s", [0, True]),
        ("times_s", [np.array(False), 1]),
        ("times_s", np.array([0.0 + 0.0j, 1.0 + 0.0j])),
        ("times_s", np.array([0.0, 1.0], dtype=object)),
        ("states", [["7000000", 0, 0, 0, 7500, 0]] * 2),
        ("states", np.ones((2, 6), dtype=bool)),
        ("states", np.ones((2, 6), dtype=np.complex128)),
        ("states", np.array([[7_000_000, 0, 0, 0, 7_500, 0]] * 2, dtype=object)),
    ],
)
def test_trajectory_diagnostics_reject_incompatible_input_representations(argument, value):
    times = np.array([0.0, 1.0], dtype=np.float64)
    states = np.array(
        [
            [7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0],
            [7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0],
        ],
        dtype=np.float64,
    )
    if argument == "times_s":
        times = value
    else:
        states = value

    with pytest.raises(ValueError, match="real numeric values"):
        diagnose_trajectory(times, states, EARTH_MU_M3_S2)


@pytest.mark.parametrize("dtype", [np.float64, np.float32, np.int64])
def test_trajectory_diagnostics_accept_real_numeric_inputs_as_float64(dtype):
    times = np.array([0, 1], dtype=dtype)
    states = np.array(
        [
            [7_000_000, 0, 0, 0, 7_500, 0],
            [7_000_000, 0, 0, 0, 7_500, 0],
        ],
        dtype=dtype,
    )

    diagnostics = diagnose_trajectory(times, states, EARTH_MU_M3_S2)

    assert diagnostics["specific_energy_m2_s2"].dtype == np.float64
    assert diagnostics["radius_m"].dtype == np.float64
    assert diagnostics["specific_energy_m2_s2"].shape == (2,)
    assert diagnostics["radius_m"].tolist() == [7_000_000.0, 7_000_000.0]


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


def test_numerical_error_policy_is_localized_and_does_not_leak_plain_floats():
    old_settings = np.seterr(all="raise")
    try:
        with pytest.raises(ValueError, match="Acceleration magnitude underflows float64"):
            two_body_derivative(
                np.array([1.0e308, 0.0, 0.0, 0.0, 1.0, 0.0], dtype=np.float64),
                EARTH_MU_M3_S2,
            )

        diagnostics = diagnose_trajectory(
            np.array([0.0, 1.0], dtype=np.float64),
            np.array(
                [
                    [7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0],
                    [7_000_000.0, 0.0, 0.0, 0.0, 7_500.0, 0.0],
                ],
                dtype=np.float64,
            ),
            EARTH_MU_M3_S2,
        )
        assert np.all(np.isfinite(diagnostics["specific_energy_m2_s2"]))
    finally:
        np.seterr(**old_settings)
