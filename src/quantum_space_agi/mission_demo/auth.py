"""Clerk session-token verification for the Mission Demo API."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import jwt
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError, PyJWTError

_ALLOWED_JWT_ALGORITHMS = ("RS256",)
_REQUIRED_CLAIMS = ("exp", "iat", "iss", "sid", "sub")
_MAX_TOKEN_LENGTH = 16_384
_JWKS_CACHE_SECONDS = 300
_JWKS_TIMEOUT_SECONDS = 5


class InvalidSessionToken(Exception):
    """The supplied Clerk session token is malformed or invalid."""


class ForbiddenAuthorizedParty(Exception):
    """The authenticated session token came from a disallowed party."""


class ClerkVerificationUnavailable(Exception):
    """Clerk verification configuration or key service is unavailable."""


def _normalize_origin(value: str, *, setting: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{setting} must contain an HTTP(S) origin only")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{setting} contains an invalid port") from exc

    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    default_port = 443 if parsed.scheme == "https" else 80
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme.lower()}://{host}{port_suffix}"


@dataclass(frozen=True, slots=True)
class ClerkAuthSettings:
    publishable_key: str | None
    frontend_api_url: str | None
    audience: str | None
    allowed_origins: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.publishable_key is not None and not self.publishable_key.strip():
            raise ValueError("CLERK_PUBLISHABLE_KEY must not be empty")
        if self.frontend_api_url is not None:
            object.__setattr__(
                self,
                "frontend_api_url",
                _normalize_origin(
                    self.frontend_api_url, setting="CLERK_FRONTEND_API_URL"
                ),
            )
        if self.audience is not None and not self.audience.strip():
            raise ValueError("CLERK_AUDIENCE must not be empty when set")

        normalized_origins = tuple(
            dict.fromkeys(
                _normalize_origin(origin, setting="CLERK_ALLOWED_ORIGINS")
                for origin in self.allowed_origins
            )
        )
        if any("*" in origin for origin in normalized_origins):
            raise ValueError("CLERK_ALLOWED_ORIGINS must not contain wildcards")
        object.__setattr__(self, "allowed_origins", normalized_origins)

    @classmethod
    def from_environment(
        cls, environ: Mapping[str, str] | None = None
    ) -> ClerkAuthSettings:
        values = os.environ if environ is None else environ

        def optional_value(name: str) -> str | None:
            value = values.get(name, "").strip()
            return value or None

        raw_origins = optional_value("CLERK_ALLOWED_ORIGINS")
        origins = (
            tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
            if raw_origins is not None
            else ()
        )
        return cls(
            publishable_key=optional_value("CLERK_PUBLISHABLE_KEY"),
            frontend_api_url=optional_value("CLERK_FRONTEND_API_URL"),
            audience=optional_value("CLERK_AUDIENCE"),
            allowed_origins=origins,
        )

    @property
    def issuer(self) -> str | None:
        return self.frontend_api_url

    @property
    def jwks_url(self) -> str | None:
        if self.frontend_api_url is None:
            return None
        return f"{self.frontend_api_url}/.well-known/jwks.json"

    @property
    def frontend_configured(self) -> bool:
        return self.publishable_key is not None and self.frontend_api_url is not None

    @property
    def configured(self) -> bool:
        return self.frontend_configured and bool(self.allowed_origins)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: str
    session_id: str
    authorized_party: str | None


class ClerkTokenVerifier:
    """Verify Clerk session JWTs against the configured Frontend API JWKS."""

    def __init__(
        self,
        settings: ClerkAuthSettings,
        *,
        jwks_client: Any | None = None,
    ) -> None:
        self.settings = settings
        if jwks_client is not None:
            self._jwks_client = jwks_client
        elif settings.configured and settings.jwks_url is not None:
            self._jwks_client = jwt.PyJWKClient(
                settings.jwks_url,
                cache_jwk_set=True,
                lifespan=_JWKS_CACHE_SECONDS,
                timeout=_JWKS_TIMEOUT_SECONDS,
            )
        else:
            self._jwks_client = None

    def verify(self, token: str) -> AuthenticatedUser:
        if not self.settings.configured or self._jwks_client is None:
            raise ClerkVerificationUnavailable(
                "Clerk session verification is not configured"
            )
        if not isinstance(token, str) or not token or len(token) > _MAX_TOKEN_LENGTH:
            raise InvalidSessionToken("Invalid Clerk session token")

        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(_ALLOWED_JWT_ALGORITHMS),
                issuer=self.settings.issuer,
                audience=self.settings.audience,
                options={
                    "require": list(_REQUIRED_CLAIMS),
                    "verify_aud": self.settings.audience is not None,
                },
            )
        except PyJWKClientConnectionError as exc:
            raise ClerkVerificationUnavailable(
                "Clerk signing keys are temporarily unavailable"
            ) from exc
        except OSError as exc:
            raise ClerkVerificationUnavailable(
                "Clerk signing keys are temporarily unavailable"
            ) from exc
        except (PyJWKClientError, PyJWTError, ValueError, TypeError) as exc:
            raise InvalidSessionToken("Invalid Clerk session token") from exc

        subject = claims.get("sub")
        session_id = claims.get("sid")
        if (
            not isinstance(subject, str)
            or not subject
            or not isinstance(session_id, str)
            or not session_id
        ):
            raise InvalidSessionToken("Invalid Clerk session token")

        authorized_party = claims.get("azp")
        if authorized_party is not None:
            if not isinstance(authorized_party, str):
                raise InvalidSessionToken("Invalid Clerk session token")
            if authorized_party not in self.settings.allowed_origins:
                raise ForbiddenAuthorizedParty("Unauthorized Clerk session origin")

        return AuthenticatedUser(
            user_id=subject,
            session_id=session_id,
            authorized_party=authorized_party,
        )
