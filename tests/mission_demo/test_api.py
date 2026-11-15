from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from quantum_space_agi.mission_demo.api import create_app
from quantum_space_agi.mission_demo.auth import ClerkAuthSettings, ClerkTokenVerifier
from quantum_space_agi.mission_demo.service import MissionDemoService

VALID_REQUEST = {
    "destination_profile_id": "synthetic-leo-400-km",
    "selected_payload_ids": ["relay", "imager"],
}


class SyncASGIClient:
    def __init__(self, app: Any, headers: dict[str, str] | None = None) -> None:
        self._app = app
        self._headers = headers

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("OPTIONS", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if self._headers is not None:
            request_headers = dict(self._headers)
            request_headers.update(kwargs.pop("headers", {}))
            kwargs["headers"] = request_headers

        async def send() -> httpx.Response:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(
                    app=self._app, raise_app_exceptions=False
                ),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())


class FixedKeyResolver:
    def __init__(self, public_key: Any) -> None:
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
        return SimpleNamespace(key=self._public_key)


class FailingKeyResolver:
    def get_signing_key_from_jwt(self, token: str) -> None:
        raise OSError("JWKS service unavailable")


def _test_token(
    signing_key: Any,
    changes: dict[str, Any] | None = None,
) -> str:
    claims: dict[str, Any] = {
        "iss": "https://clerk.example",
        "exp": 4_000_000_000,
        "iat": 1_700_000_000,
        "sub": "user_test_123",
        "sid": "sess_test_123",
        "azp": "https://app.example",
    }
    claims.update(changes or {})
    return jwt.encode(
        claims,
        signing_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def _authenticated_client(
    auth_settings: ClerkAuthSettings,
    signing_key: Any,
    *,
    service: MissionDemoService | None = None,
    token_verifier: Any | None = None,
    token: str | None = None,
) -> SyncASGIClient:
    verifier = (
        ClerkTokenVerifier(
            auth_settings,
            jwks_client=FixedKeyResolver(signing_key.public_key()),
        )
        if token_verifier is None
        else token_verifier
    )
    session_token = _test_token(signing_key) if token is None else token
    return SyncASGIClient(
        create_app(service, auth_settings=auth_settings, token_verifier=verifier),
        headers={"Authorization": f"Bearer {session_token}"},
    )


@pytest.fixture
def auth_settings() -> ClerkAuthSettings:
    return ClerkAuthSettings(
        publishable_key="pk_test_example",
        frontend_api_url="https://clerk.example",
        audience=None,
        allowed_origins=("https://app.example",),
    )


@pytest.fixture
def signing_key() -> Any:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def authenticated_client(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> SyncASGIClient:
    return _authenticated_client(auth_settings, signing_key)


def test_health_destinations_and_dashboard_are_served_locally() -> None:
    client = SyncASGIClient(create_app())

    assert client.get("/health").json() == {"status": "ok"}
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert 'id="mission-demo-form"' in dashboard.text


def test_mission_routes_require_authentication() -> None:
    client = SyncASGIClient(create_app())
    responses = [
        client.get("/api/v1/missions/destinations"),
        client.post("/api/v1/missions/validate", json=VALID_REQUEST),
        client.post("/api/v1/missions/run", json=VALID_REQUEST),
    ]

    assert [response.status_code for response in responses] == [401, 401, 401]
    assert all(
        response.json()["error"]["code"] == "authentication_required"
        for response in responses
    )


def test_valid_session_can_access_each_mission_route(
    authenticated_client: SyncASGIClient,
) -> None:
    client = authenticated_client
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
    assert (
        client.post("/api/v1/missions/validate", json=VALID_REQUEST).status_code == 200
    )
    assert client.post("/api/v1/missions/run", json=VALID_REQUEST).status_code == 200


def test_auth_config_is_public_and_disabled_without_clerk_settings() -> None:
    response = SyncASGIClient(create_app()).get("/api/v1/auth/config")

    assert response.status_code == 200
    assert response.json() == {"enabled": False}


def test_auth_config_exposes_only_public_clerk_settings(
    auth_settings: ClerkAuthSettings,
) -> None:
    response = SyncASGIClient(create_app(auth_settings=auth_settings)).get(
        "/api/v1/auth/config"
    )

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "publishable_key": "pk_test_example",
        "frontend_api_url": "https://clerk.example",
    }
    assert "secret" not in response.text.lower()


@pytest.mark.parametrize(
    "authorization",
    ["Basic test-credentials", "Bearer malformed-sensitive-token"],
)
def test_malformed_credentials_are_rejected_without_reflection(
    authorization: str, authenticated_client: SyncASGIClient
) -> None:
    response = authenticated_client.get(
        "/api/v1/missions/destinations",
        headers={"Authorization": authorization},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_session_token"
    assert authorization.removeprefix("Bearer ") not in response.text


def test_invalid_signature_is_rejected(
    authenticated_client: SyncASGIClient,
) -> None:
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _test_token(wrong_key)
    response = authenticated_client.get(
        "/api/v1/missions/destinations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_session_token"
    assert token not in response.text


def test_disallowed_authorized_party_returns_forbidden(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> None:
    token = _test_token(signing_key, {"azp": "https://other.example"})
    response = _authenticated_client(auth_settings, signing_key, token=token).get(
        "/api/v1/missions/destinations"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert token not in response.text


def test_jwks_outage_fails_closed_with_service_unavailable(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> None:
    verifier = ClerkTokenVerifier(auth_settings, jwks_client=FailingKeyResolver())
    response = _authenticated_client(
        auth_settings, signing_key, token_verifier=verifier
    ).get("/api/v1/missions/destinations")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "authentication_unavailable"


def test_unconfigured_verification_fails_closed() -> None:
    settings = ClerkAuthSettings(
        publishable_key=None,
        frontend_api_url=None,
        audience=None,
        allowed_origins=(),
    )
    client = SyncASGIClient(
        create_app(auth_settings=settings),
        headers={"Authorization": "Bearer provided-token"},
    )

    response = client.get("/api/v1/missions/destinations")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "authentication_unavailable"
    assert "provided-token" not in response.text


def test_cors_allows_only_configured_origins(
    auth_settings: ClerkAuthSettings,
) -> None:
    client = SyncASGIClient(create_app(auth_settings=auth_settings))
    allowed = client.options(
        "/api/v1/missions/run",
        headers={
            "Origin": "https://app.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    denied = client.options(
        "/api/v1/missions/run",
        headers={
            "Origin": "https://other.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://app.example"
    assert "access-control-allow-credentials" not in allowed.headers
    assert allowed.headers["x-content-type-options"] == "nosniff"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_baseline_security_headers_are_added_to_public_and_error_responses() -> None:
    client = SyncASGIClient(create_app())

    for path in ("/health", "/", "/mission-demo.js", "/api/v1/auth/config"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert response.headers["x-frame-options"] == "DENY"

    protected_error = client.get("/api/v1/missions/destinations")
    assert protected_error.status_code == 401
    assert protected_error.headers["x-frame-options"] == "DENY"


def test_authentication_failure_does_not_log_bearer_token(
    caplog: pytest.LogCaptureFixture, authenticated_client: SyncASGIClient
) -> None:
    token = "sensitive-test-token"
    authenticated_client.get(
        "/api/v1/missions/destinations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert token not in caplog.text


def test_validate_returns_canonical_mission_without_running_simulation(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> None:
    class RunMustNotBeCalled(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            pytest.fail("validation endpoint must not execute a mission")

    client = _authenticated_client(
        auth_settings, signing_key, service=RunMustNotBeCalled()
    )
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


def test_run_returns_actual_arc05_and_arc08_results(
    authenticated_client: SyncASGIClient,
) -> None:
    client = authenticated_client
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
    mission_payload: dict[str, Any],
    field: str,
    authenticated_client: SyncASGIClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/missions/validate", json=mission_payload
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert any(field in detail["field"] for detail in error["details"])


def test_malformed_json_and_unsupported_media_type_have_explicit_errors(
    authenticated_client: SyncASGIClient,
) -> None:
    client = authenticated_client

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


def test_run_hides_internal_failure_details(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> None:
    class FailingService(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("private implementation detail")

    response = _authenticated_client(
        auth_settings, signing_key, service=FailingService()
    ).post("/api/v1/missions/run", json=VALID_REQUEST)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "mission_run_failed"
    assert "private implementation detail" not in response.text


def test_run_rejects_non_finite_simulation_output(
    auth_settings: ClerkAuthSettings, signing_key: Any
) -> None:
    class NonFiniteService(MissionDemoService):
        def run(self, request: dict[str, Any]) -> dict[str, Any]:
            result = super().run(request)
            result["trajectory"]["states"][0][0] = float("nan")
            return result

    response = _authenticated_client(
        auth_settings, signing_key, service=NonFiniteService()
    ).post("/api/v1/missions/run", json=VALID_REQUEST)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "mission_run_failed"
    assert "NaN" not in response.text
