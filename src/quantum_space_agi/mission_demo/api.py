"""Versioned loopback API for the local educational mission dashboard."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

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
) -> JSONResponse:
    payload = ApiErrorDTO(
        error=ApiErrorDetailDTO(
            code=code,
            message=message,
            details=[] if details is None else details,
        )
    )
    return JSONResponse(
        status_code=status_code, content=payload.model_dump(mode="json")
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


def create_app(service: MissionDemoService | None = None) -> FastAPI:
    """Create the local mission API with an injectable domain service."""
    mission_service = MissionDemoService() if service is None else service
    application = FastAPI(
        title="NASAQ26 Local Mission API",
        version="1.0.0",
        description="Synthetic educational mission simulation; local use only.",
    )

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
        }.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "The request failed."
        return _error_response(exc.status_code, code, message)

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

    @application.get("/api/v1/missions/destinations", response_model=DestinationListDTO)
    async def destinations() -> DestinationListDTO:
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
    async def validate_mission(request: MissionRequestDTO) -> MissionValidationDTO:
        return MissionValidationDTO(valid=True, mission=_mission_summary(request))

    @application.post("/api/v1/missions/run", response_model=MissionRunResponseDTO)
    async def run_mission(request: MissionRequestDTO) -> MissionRunResponseDTO:
        result: dict[str, Any] = mission_service.run(request.model_dump(mode="json"))
        return MissionRunResponseDTO.model_validate(result)

    application.mount(
        "/", StaticFiles(directory=str(_FRONTEND_ROOT), html=True), name="dashboard"
    )
    return application


app = create_app()
