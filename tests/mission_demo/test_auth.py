from __future__ import annotations

import importlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
from threading import Thread
from types import SimpleNamespace
from typing import Any

import jwt
import jwt.jwks_client
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

DEFAULT_CLAIMS: dict[str, Any] = {
    "iss": "https://clerk.example",
    "exp": 4_000_000_000,
    "iat": 1_700_000_000,
    "sub": "user_test_123",
    "sid": "sess_test_123",
    "azp": "https://app.example",
}
AUTH_MODULE_AVAILABLE = find_spec("quantum_space_agi.mission_demo.auth") is not None


def load_auth_module() -> Any:
    module_name = "quantum_space_agi.mission_demo.auth"
    assert find_spec(module_name) is not None, (
        "Clerk authentication verifier is missing"
    )
    return importlib.import_module(module_name)


class FixedKeyResolver:
    def __init__(self, public_key: Any) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
        return SimpleNamespace(key=self.public_key)


class FailingKeyResolver:
    def get_signing_key_from_jwt(self, token: str) -> None:
        raise OSError("JWKS service unavailable")


def encode_test_token(
    signing_key: Any,
    changes: dict[str, Any] | None = None,
    *,
    algorithm: str = "RS256",
) -> str:
    payload = DEFAULT_CLAIMS.copy()
    for name, value in (changes or {}).items():
        if value is None:
            payload.pop(name, None)
        else:
            payload[name] = value
    return jwt.encode(
        payload,
        signing_key,
        algorithm=algorithm,
        headers={"kid": "test-key"},
    )


def make_settings(
    auth_module: Any,
    *,
    frontend_api_url: str = "https://clerk.example",
    audience: str | None = None,
    allowed_origins: tuple[str, ...] = ("https://app.example",),
) -> Any:
    return auth_module.ClerkAuthSettings(
        publishable_key="pk_test_example",
        frontend_api_url=frontend_api_url,
        audience=audience,
        allowed_origins=allowed_origins,
    )


@pytest.fixture(scope="module")
def signing_key() -> Any:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def auth_module() -> Any:
    return load_auth_module()


@pytest.fixture
def verifier(auth_module: Any, signing_key: Any) -> Any:
    return auth_module.ClerkTokenVerifier(
        make_settings(auth_module),
        jwks_client=FixedKeyResolver(signing_key.public_key()),
    )


def test_clerk_auth_module_is_available() -> None:
    assert AUTH_MODULE_AVAILABLE, "Clerk authentication verifier is missing"


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_verifies_a_valid_session_token(verifier: Any, signing_key: Any) -> None:
    user = verifier.verify(encode_test_token(signing_key))

    assert user.user_id == "user_test_123"
    assert user.session_id == "sess_test_123"
    assert user.authorized_party == "https://app.example"


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_loads_clerk_configuration_from_environment(
    auth_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_test_example")
    monkeypatch.setenv("CLERK_FRONTEND_API_URL", "https://clerk.example")
    monkeypatch.setenv("CLERK_AUDIENCE", "mission-demo")
    monkeypatch.setenv("CLERK_ALLOWED_ORIGINS", "https://app.example")

    settings = auth_module.ClerkAuthSettings.from_environment()

    assert settings.audience == "mission-demo"
    assert settings.allowed_origins == ("https://app.example",)
    assert settings.issuer == "https://clerk.example"
    assert settings.jwks_url == "https://clerk.example/.well-known/jwks.json"


def test_rejects_non_loopback_http_frontend_api_url(auth_module: Any) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        make_settings(auth_module, frontend_api_url="http://clerk.example")


def test_allows_loopback_http_frontend_api_url_for_local_verification(
    auth_module: Any,
) -> None:
    settings = make_settings(auth_module, frontend_api_url="http://127.0.0.1:8080")

    assert settings.frontend_api_url == "http://127.0.0.1:8080"


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://other.example"},
        {"exp": 1},
        {"sub": None},
        {"sid": None},
        {"nbf": 4_000_000_000},
    ],
)
@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_rejects_invalid_or_incomplete_session_claims(
    verifier: Any, signing_key: Any, changes: dict[str, Any]
) -> None:
    auth_module = load_auth_module()

    with pytest.raises(auth_module.InvalidSessionToken):
        verifier.verify(encode_test_token(signing_key, changes))


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_rejects_invalid_signature(auth_module: Any, signing_key: Any) -> None:
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = auth_module.ClerkTokenVerifier(
        make_settings(auth_module),
        jwks_client=FixedKeyResolver(signing_key.public_key()),
    )

    with pytest.raises(auth_module.InvalidSessionToken):
        verifier.verify(encode_test_token(wrong_key))


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_rejects_unconfigured_jwt_algorithm(auth_module: Any, verifier: Any) -> None:
    token = jwt.encode(
        DEFAULT_CLAIMS,
        "test-only-hmac-key-material-for-hs256",
        algorithm="HS256",
        headers={"kid": "test-key"},
    )

    with pytest.raises(auth_module.InvalidSessionToken):
        verifier.verify(token)


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_rejects_wrong_audience_when_audience_is_configured(
    auth_module: Any, signing_key: Any
) -> None:
    verifier = auth_module.ClerkTokenVerifier(
        make_settings(auth_module, audience="mission-demo"),
        jwks_client=FixedKeyResolver(signing_key.public_key()),
    )
    token = encode_test_token(signing_key, {"aud": "another-service"})

    with pytest.raises(auth_module.InvalidSessionToken):
        verifier.verify(token)


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_rejects_a_valid_token_from_a_disallowed_authorized_party(
    auth_module: Any, signing_key: Any, verifier: Any
) -> None:
    token = encode_test_token(signing_key, {"azp": "https://other.example"})

    with pytest.raises(auth_module.ForbiddenAuthorizedParty):
        verifier.verify(token)


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_fails_closed_when_jwks_resolution_fails(
    auth_module: Any, signing_key: Any
) -> None:
    verifier = auth_module.ClerkTokenVerifier(
        make_settings(auth_module),
        jwks_client=FailingKeyResolver(),
    )

    with pytest.raises(auth_module.ClerkVerificationUnavailable):
        verifier.verify(encode_test_token(signing_key))


def _jwk(public_key: Any, kid: str) -> dict[str, Any]:
    result = jwt.algorithms.RSAAlgorithm.to_jwk(public_key, as_dict=True)
    result.update({"kid": kid, "alg": "RS256", "use": "sig"})
    return result


@pytest.mark.skipif(
    not AUTH_MODULE_AVAILABLE, reason="verifier module not implemented yet"
)
def test_pyjwkclient_refreshes_jwks_for_rotated_key(
    signing_key: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_time = [0.0]
    monkeypatch.setattr(
        jwt.jwks_client,
        "time",
        SimpleNamespace(monotonic=lambda: current_time[0]),
    )
    auth_module = load_auth_module()
    rotated_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks_payloads = [
        {"keys": [_jwk(signing_key.public_key(), "key-a")]},
        {
            "keys": [
                _jwk(signing_key.public_key(), "key-a"),
                _jwk(rotated_key.public_key(), "key-b"),
            ]
        },
    ]
    request_count = 0

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            nonlocal request_count
            payload = jwks_payloads[min(request_count, len(jwks_payloads) - 1)]
            request_count += 1
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    frontend_api_url = f"http://127.0.0.1:{server.server_port}"
    settings = make_settings(
        auth_module,
        frontend_api_url=frontend_api_url,
        allowed_origins=("https://app.example",),
    )
    verifier = auth_module.ClerkTokenVerifier(settings)

    try:
        key_a_token = jwt.encode(
            {**DEFAULT_CLAIMS, "iss": frontend_api_url},
            signing_key,
            algorithm="RS256",
            headers={"kid": "key-a"},
        )
        key_b_token = jwt.encode(
            {**DEFAULT_CLAIMS, "iss": frontend_api_url},
            rotated_key,
            algorithm="RS256",
            headers={"kid": "key-b"},
        )

        assert verifier.verify(key_a_token).user_id == "user_test_123"
        current_time[0] = 31.0
        assert verifier.verify(key_b_token).user_id == "user_test_123"
        assert request_count == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
