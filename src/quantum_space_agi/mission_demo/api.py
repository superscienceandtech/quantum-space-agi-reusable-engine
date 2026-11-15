"""Versioned loopback API for the local educational mission dashboard."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from .auth import (
    AuthenticatedUser,
    ClerkAuthSettings,
    ClerkTokenVerifier,
    ClerkVerificationUnavailable,
    ForbiddenAuthorizedParty,
    InvalidSessionToken,
)
from .configuration import (
    ORBIT_DESTINATION_PROFILES,
    MissionDemoConfiguration,
    SpacecraftConfiguration,
)
from .dto import (
    ApiErrorDetailDTO,
    ApiErrorDTO,
    ApiErrorFieldDTO,
    DestinationListDTO,
    DestinationProfileDTO,
    MissionRequestDTO,
    MissionRunResponseDTO,
    MissionSummaryDTO,
    MissionValidationDTO,
)
from .rate_limit import FixedWindowRateLimiter
from .service import MissionDemoService

logger = logging.getLogger(__name__)
_FRONTEND_ROOT = Path(__file__).resolve().parents[3] / "arc09-ui-prototype"
_MISSION_POST_PATHS = {
    "/api/v1/missions/validate",
    "/api/v1/missions/run",
}


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[ApiErrorFieldDTO] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    payload = ApiErrorDTO(
        error=ApiErrorDetailDTO(
            code=code,
            message=message,
            details=[] if details is None else details,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )


def _mission_summary(request: MissionRequestDTO) -> MissionSummaryDTO:
    spacecraft = SpacecraftConfiguration(request.selected_payload_ids)
    mission = MissionDemoConfiguration(request.destination_profile_id, spacecraft)
    profile = mission.destination_profile
    return MissionSummaryDTO(
        destination_profile_id=profile.profile_id,
        destination_display_name=profile.display_name,
        spacecraft_profile_id=spacecraft.profile_id,
        selected_payload_ids=list(spacecraft.selected_payload_ids),
    )


def create_app(
    service: MissionDemoService | None = None,
    auth_settings: ClerkAuthSettings | None = None,
    token_verifier: ClerkTokenVerifier | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Create the mission API with injectable domain and auth dependencies."""
    mission_service = MissionDemoService() if service is None else service
    settings = (
        ClerkAuthSettings.from_environment() if auth_settings is None else auth_settings
    )
    verifier = (
        ClerkTokenVerifier(settings) if token_verifier is None else token_verifier
    )
    mission_rate_limiter = (
        FixedWindowRateLimiter() if rate_limiter is None else rate_limiter
    )
    application = FastAPI(
        title="NASAQ26 Local Mission API",
        version="1.0.0",
        description="Synthetic educational mission simulation; local use only.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )

    @application.middleware("http")
    async def security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
        if request.method == "POST" and request.url.path in _MISSION_POST_PATHS:
            if content_type != "application/json":
                return _error_response(
                    415,
                    "unsupported_media_type",
                    "Send mission requests as application/json.",
                )

        validation_errors = exc.errors()
        if any(error.get("type") == "json_invalid" for error in validation_errors):
            return _error_response(
                400, "malformed_json", "The request body is not valid JSON."
            )

        details = [
            ApiErrorFieldDTO(
                field=".".join(
                    str(part) for part in error.get("loc", ()) if part != "body"
                )
                or "request",
                message=str(error.get("msg", "Invalid value.")),
            )
            for error in validation_errors
        ]
        return _error_response(
            422,
            "validation_error",
            "The mission request did not pass validation.",
            details,
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = {
            404: "not_found",
            405: "method_not_allowed",
            401: "authentication_required",
            403: "forbidden",
            503: "authentication_unavailable",
            429: "rate_limited",
        }.get(exc.status_code, "http_error")
        default_messages = {
            401: "A valid Clerk session token is required.",
            403: "The authenticated session is not authorized for this application.",
            503: "Authentication verification is temporarily unavailable.",
            429: "The mission request limit has been reached.",
        }
        message = default_messages.get(exc.status_code, "The request failed.")
        if isinstance(exc.detail, str) and exc.status_code not in default_messages:
            message = exc.detail
        elif isinstance(exc.detail, dict):
            detail_code = exc.detail.get("code")
            detail_message = exc.detail.get("message")
            if isinstance(detail_code, str):
                code = detail_code
            if isinstance(detail_message, str):
                message = detail_message
        return _error_response(exc.status_code, code, message, headers=exc.headers)

    @application.exception_handler(Exception)
    async def unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Local mission API request failed", exc_info=exc)
        return _error_response(
            500,
            "mission_run_failed",
            "The educational mission run could not be completed.",
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/v1/auth/config")
    async def auth_config() -> dict[str, Any]:
        if not settings.configured:
            return {"enabled": False}
        return {
            "enabled": True,
            "publishable_key": settings.publishable_key,
            "frontend_api_url": settings.frontend_api_url,
        }

    def require_authenticated_user(
        authorization: str | None = Header(default=None),
    ) -> AuthenticatedUser:
        if authorization is None or not authorization.strip():
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "authentication_required",
                    "message": "A valid Clerk session token is required.",
                },
            )
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "invalid_session_token",
                    "message": "A valid Clerk session token is required.",
                },
            )
        try:
            return verifier.verify(parts[1])
        except InvalidSessionToken as exc:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "invalid_session_token",
                    "message": "A valid Clerk session token is required.",
                },
            ) from exc
        except ForbiddenAuthorizedParty as exc:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "forbidden",
                    "message": (
                        "The authenticated session is not authorized for this "
                        "application."
                    ),
                },
            ) from exc
        except ClerkVerificationUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "authentication_unavailable",
                    "message": (
                        "Authentication verification is temporarily unavailable."
                    ),
                },
            ) from exc

    def enforce_rate_limit(user: AuthenticatedUser, route_key: str, limit: int) -> None:
        retry_after = mission_rate_limiter.check(user.user_id, route_key, limit)
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "rate_limited",
                    "message": "The mission request limit has been reached.",
                },
                headers={"Retry-After": str(retry_after)},
            )

    @application.get("/api/v1/missions/destinations", response_model=DestinationListDTO)
    async def destinations(
        user: AuthenticatedUser = Depends(require_authenticated_user),
    ) -> DestinationListDTO:
        enforce_rate_limit(user, "destinations", 60)
        return DestinationListDTO(
            destinations=[
                DestinationProfileDTO(
                    profile_id=profile.profile_id,
                    display_name=profile.display_name,
                    altitude_m=profile.altitude_m,
                    simulation_duration_s=profile.simulation_duration_s,
                    time_step_s=profile.time_step_s,
                    assumptions=list(profile.assumptions),
                    classification=profile.classification,
                )
                for profile in ORBIT_DESTINATION_PROFILES.values()
            ]
        )

    @application.post("/api/v1/missions/validate", response_model=MissionValidationDTO)
    async def validate_mission(
        request: MissionRequestDTO,
        user: AuthenticatedUser = Depends(require_authenticated_user),
    ) -> MissionValidationDTO:
        enforce_rate_limit(user, "validate", 30)
        return MissionValidationDTO(valid=True, mission=_mission_summary(request))

    @application.post("/api/v1/missions/run", response_model=MissionRunResponseDTO)
    async def run_mission(
        request: MissionRequestDTO,
        user: AuthenticatedUser = Depends(require_authenticated_user),
    ) -> MissionRunResponseDTO:
        enforce_rate_limit(user, "run", 5)
        result: dict[str, Any] = mission_service.run(request.model_dump(mode="json"))
        return MissionRunResponseDTO.model_validate(result)

    application.mount(
        "/", StaticFiles(directory=str(_FRONTEND_ROOT), html=True), name="dashboard"
    )
    return application


app = create_app()
