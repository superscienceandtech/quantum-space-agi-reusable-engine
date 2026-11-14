from __future__ import annotations

import uvicorn

from quantum_space_agi.mission_demo import server


def test_server_entry_point_binds_only_to_loopback(monkeypatch) -> None:
    calls: list[tuple[object, dict[str, object]]] = []
    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda app, **kwargs: calls.append((app, kwargs)),
    )

    server.main()

    assert len(calls) == 1
    app, options = calls[0]
    assert app == "quantum_space_agi.mission_demo.api:app"
    assert options == {"host": "127.0.0.1", "port": 8765}
