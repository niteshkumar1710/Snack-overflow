from typing import Any, Dict
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Custom application exception with structured error format."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        message: str = "A business error occurred.",
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Format custom application exceptions according to the API contract."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format FastAPI validation errors according to the API contract."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    msg = first_error.get("msg", "Invalid request parameters")
    loc = " -> ".join(str(loc_item) for loc_item in first_error.get("loc", []))
    formatted_msg = f"{loc}: {msg}" if loc else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": formatted_msg,
            }
        },
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Format unhandled server exceptions cleanly without leaking internal secrets."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
            }
        },
    )
