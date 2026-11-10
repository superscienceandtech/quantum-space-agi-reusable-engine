"""Public ML package imports keep separate evaluator modules lazy."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_offline_ml_package_import_does_not_eagerly_import_mission_evaluator() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    script = """
import sys
import quantum_space_agi.ml as ml

assert callable(ml.validate_baseline_dataset)
assert callable(ml.prepare_regression_dataset)
assert callable(ml.evaluate_regression_model)
assert callable(ml.calculate_regression_metrics)
assert callable(ml.prepare_and_evaluate_regression)
assert callable(ml.ingest_votable_payload)
assert callable(ml.split_by_host)
assert callable(ml.write_snapshot_artifact)
assert not any(
    name in sys.modules
    for name in (
        "quantum_space_agi.ml.mission_configuration",
        "quantum_space_agi.ml.mission_evaluator",
        "quantum_space_agi.ml.mission_scenarios",
    )
)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository_root / "src")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_educational_evaluator_public_exports_remain_compatible() -> None:
    from quantum_space_agi.ml import (
        EducationalMissionConfiguration,
        evaluate_educational_mission,
    )
    from quantum_space_agi.ml.mission_configuration import (
        EducationalMissionConfiguration as ModuleConfiguration,
    )
    from quantum_space_agi.ml.mission_evaluator import (
        evaluate_educational_mission as module_evaluate,
    )

    assert EducationalMissionConfiguration is ModuleConfiguration
    assert evaluate_educational_mission is module_evaluate
