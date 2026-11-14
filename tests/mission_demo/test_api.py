from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from quantum_space_agi.mission_demo.api import create_app
from quantum_space_agi.mission_demo.service import MissionDemoService

VALID_REQUEST = {
    "destination_profile_id": "synthetic-leo-400-km",
    "selected_payload_ids": ["relay", "imager"],
}


class SyncASGIClient:
    def __init__(self, app: Any) -> None:
        self._app = app

    def get(self, path: str) -> httpx.Response:
        return self._request("GET", path)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async def send() -> httpx.Response:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(
                    app=self._app, raise_app_exceptions=False
                ),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())


def test_health_destinations_and_dashboard_are_served_locally() -> None:
    client = SyncASGIClient(create_app())

    assert client.get("/health").json() == {"status": "ok"}
    destinations = client.get("/api/v1/missions/destinations")

    assert destinations.status_code == 200
    assert {
        profile["profile_id"] for profile in destinations.json()["destinations"]
    } == {
        "synthetic-leo-400-km",
        "synthetic-leo-800-km",
        "synthetic-earth-orbit-2000-km",
    }
    assert all(
        profile["classification"] == "synthetic educational profile"
        for profile in destinations.json()["destinations"]
    )
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert 'id="mission-demo-form"' in dashboard.text


def test_validate_returns_canonical_mission_without_running_simulation() -> None:
    class RunMustNotBeCalled(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            pytest.fail("validation endpoint must not execute a mission")

    client = SyncASGIClient(create_app(RunMustNotBeCalled()))
    response = client.post("/api/v1/missions/validate", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "mission": {
            "destination_profile_id": "synthetic-leo-400-km",
            "destination_display_name": "Synthetic LEO profile A",
            "spacecraft_profile_id": "educational-payload-carrier-v1",
            "selected_payload_ids": ["imager", "relay"],
        },
    }


def test_run_returns_actual_arc05_and_arc08_results() -> None:
    client = SyncASGIClient(create_app())
    response = client.post("/api/v1/missions/run", json=VALID_REQUEST)

    assert response.status_code == 200
    result = response.json()
    trajectory = result["trajectory"]
    assert trajectory["states"][0][:3] == [6_778_137.0, 0.0, 0.0]
    assert trajectory["model"]["reference_frame"] == "ECI"
    assert trajectory["model"]["integrator"] == "RK4"
    assert len(trajectory["times_s"]) == len(trajectory["states"])
    assert trajectory["diagnostics"]["radius_m"][0] == pytest.approx(6_778_137.0)
    assert result["resource_evaluation"]["status"] == "evaluated"
    assert result["resource_evaluation"]["policy_approval_status"] == "pending"
    assert (
        result["resource_evaluation"]["result"]["scenario_id"]
        == "resource-selection-demo-v1"
    )
    assert "abstract educational units" in result["resource_evaluation"]["warning"]


@pytest.mark.parametrize(
    ("mission_payload", "field"),
    [
        (
            {
                "destination_profile_id": "synthetic-leo-400-km",
                "selected_payload_ids": [],
            },
            "selected_payload_ids",
        ),
        (
            {
                "destination_profile_id": "synthetic-leo-400-km",
                "selected_payload_ids": ["imager", "imager"],
            },
            "selected_payload_ids",
        ),
        (
            {
                "destination_profile_id": "synthetic-leo-400-km",
                "selected_payload_ids": ["unknown"],
            },
            "selected_payload_ids",
        ),
        (
            {"destination_profile_id": "mars", "selected_payload_ids": ["imager"]},
            "destination_profile_id",
        ),
        ({**VALID_REQUEST, "extra": True}, "extra"),
    ],
)
def test_validate_returns_field_errors_for_invalid_requests(
    mission_payload: dict[str, Any], field: str
) -> None:
    response = SyncASGIClient(create_app()).post(
        "/api/v1/missions/validate", json=mission_payload
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any(field in detail["field"] for detail in error["details"])


def test_malformed_json_and_unsupported_media_type_have_explicit_errors() -> None:
    client = SyncASGIClient(create_app())

    malformed = client.post(
        "/api/v1/missions/run",
        content=b"{",
        headers={"content-type": "application/json"},
    )
    unsupported = client.post(
        "/api/v1/missions/run",
        content=b"not json",
        headers={"content-type": "text/plain"},
    )

    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "malformed_json"
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "unsupported_media_type"


def test_unknown_api_route_uses_the_error_envelope() -> None:
    response = SyncASGIClient(create_app()).get("/api/v1/missions/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_run_hides_internal_failure_details() -> None:
    class FailingService(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("private implementation detail")

    response = SyncASGIClient(create_app(FailingService())).post(
        "/api/v1/missions/run", json=VALID_REQUEST
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "mission_run_failed"
    assert "private implementation detail" not in response.text


def test_run_rejects_non_finite_simulation_output() -> None:
    class NonFiniteService(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            result = super().run(request)
            result["trajectory"]["states"][0][0] = float("nan")
            return result

    response = SyncASGIClient(create_app(NonFiniteService())).post(
        "/api/v1/missions/run", json=VALID_REQUEST
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "mission_run_failed"
    assert "NaN" not in response.text
