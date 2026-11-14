from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT / "arc09-ui-prototype"


def test_dashboard_uses_local_mission_api_and_exposes_run_form() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    adapter = PROTOTYPE / "mission-demo.js"

    assert '<form id="mission-demo-form"' in html
    assert 'id="mission-demo-status"' in html
    assert 'id="mission-demo-results"' in html
    assert adapter.is_file()
    script = adapter.read_text(encoding="utf-8")
    assert "fetch('/api/v1/missions/destinations')" in script
    assert "fetch('/api/v1/missions/validate'" in script
    assert "fetch('/api/v1/missions/run'" in script
    assert "/local/mission-run" not in script
    assert "disabled>Validate and run mission</button>" in html


def test_dashboard_labels_synthetic_assumptions_and_policy_boundary() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")

    assert "Synthetic educational profiles only" in html
    assert "resource-policy approval remains pending" in html
    assert "ARC-08 runs after ARC-05" in html
    assert "No fuel estimate" in html
