"""A single, consistent error envelope for every failure the API returns."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """Raised by services and controllers to return a predictable failure.

    Example:
        raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


# Pydantic error type -> the code the API reports.
_ERROR_CODE_BY_TYPE: dict[str, str] = {
    "missing": "REQUIRED",
    "string_too_short": "TOO_SHORT",
    "string_too_long": "TOO_LONG",
    "string_pattern_mismatch": "INVALID_FORMAT",
    "greater_than": "OUT_OF_RANGE",
    "greater_than_equal": "OUT_OF_RANGE",
    "less_than": "OUT_OF_RANGE",
    "less_than_equal": "OUT_OF_RANGE",
    "too_long": "TOO_LONG",
    "too_short": "TOO_SHORT",
    "extra_forbidden": "UNKNOWN_FIELD",
    "value_error": "INVALID",
    "enum": "INVALID_CHOICE",
}


def _field_path(loc: tuple[Any, ...]) -> str:
    """Dotted field path, with the leading body/query marker removed."""
    parts = [str(p) for p in loc if p not in {"body", "query", "path", "header"}]
    return ".".join(parts) or "body"


def normalise_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert Pydantic errors into the API's field-level detail shape.

    Pydantic puts the original exception object in ``ctx``, which is not JSON
    serialisable, so raw errors cannot be returned. Normalising here also makes
    request-validation failures match the shape produced by the publish
    contract, so the frontend maps both the same way.
    """
    details: list[dict[str, str]] = []
    for error in errors:
        error_type = str(error.get("type", ""))
        details.append(
            {
                "field": _field_path(tuple(error.get("loc", ()))),
                "code": _ERROR_CODE_BY_TYPE.get(error_type, error_type.upper() or "INVALID"),
                "message": str(error.get("msg", "Invalid value.")),
            }
        )
    return details


def _envelope(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so no unformatted error ever escapes the API."""

    @app.exception_handler(ApiError)
    async def _handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(
                "VALIDATION_ERROR",
                "The request payload failed validation.",
                normalise_validation_errors(exc.errors()),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client; the traceback goes to the logs.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("INTERNAL_SERVER_ERROR", "Something went wrong."),
        )
