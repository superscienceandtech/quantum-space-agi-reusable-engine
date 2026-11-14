from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setuptools_discovers_only_real_quantum_space_agi_packages() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    discovery = config["tool"]["setuptools"]["packages"]["find"]

    assert discovery == {
        "where": ["src"],
        "include": ["quantum_space_agi*"],
        "namespaces": False,
    }

    for package in (
        "quantum_space_agi",
        "quantum_space_agi.simulation",
        "quantum_space_agi.ml",
        "quantum_space_agi.mission_demo",
    ):
        path = ROOT / "src" / Path(*package.split("."))
        assert (path / "__init__.py").is_file()
