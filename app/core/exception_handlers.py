
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.core.exceptions import AppException
from app.core.logger import get_logger


logger = get_logger("opspilot.exception_handler")


def error_response(
    status_code: int,
    error_code: str,
    message: str,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
            },
        },
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    logger.warning(
        "Application exception | method=%s | path=%s | code=%s | message=%s",
        request.method,
        request.url.path,
        exc.error_code,
        exc.message,
    )

    return error_response(
        exc.status_code,
        exc.error_code,
        exc.message,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        "Request validation failed | method=%s | path=%s | error_count=%d",
        request.method,
        request.url.path,
        len(exc.errors()),
    )

    return error_response(
        422,
        "VALIDATION_ERROR",
        "Request validation failed",
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    return error_response(
        exc.status_code,
        "HTTP_ERROR",
        str(exc.detail),
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
):
    logger.exception(
        "Database integrity violation | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    return error_response(
        409,
        "DATABASE_INTEGRITY_ERROR",
        "The operation conflicts with existing data",
    )


async def operational_exception_handler(
    request: Request,
    exc: OperationalError,
):
    logger.exception(
        "Database operational failure | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    return error_response(
        503,
        "DATABASE_UNAVAILABLE",
        "The database is temporarily unavailable",
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.exception(
        "Database error | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    return error_response(
        500,
        "DATABASE_ERROR",
        "A database operation failed",
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    return error_response(
        500,
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred",
    )
