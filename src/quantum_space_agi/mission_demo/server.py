"""Loopback-only Uvicorn entry point for the local educational mission app."""

from __future__ import annotations

import uvicorn

LOCAL_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def main() -> None:
    print(f"NASAQ26 local educational demo: http://{LOCAL_HOST}:{DEFAULT_PORT}/")
    print("Synthetic educational inputs only; no NASA data or production deployment.")
    uvicorn.run(
        "quantum_space_agi.mission_demo.api:app",
        host=LOCAL_HOST,
        port=DEFAULT_PORT,
    )


if __name__ == "__main__":
    main()
