
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logger import setup_logging

from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    integrity_exception_handler,
    operational_exception_handler,
    database_exception_handler,
    unexpected_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from app.api.v1.endpoints.applications import router as applications_router
from app.api.v1.endpoints.services import router as services_router
from app.api.v1.endpoints.monitors import router as monitors_router
from app.api.v1.endpoints.log_entries import router as log_entries_router
from app.api.v1.endpoints.incidents import router as incidents_router
from app.api.v1.endpoints.incident_events import router as incident_events_router
from app.api.v1.endpoints.incident_analyses import router as incident_analyses_router
from app.api.v1.endpoints.incident_services import router as incident_services_router
from app.api.v1.endpoints.service_dependencies import router as service_dependencies_router
from app.api.v1.endpoints.monitor_checks import router as monitor_checks_router
from app.api.v1.endpoints.incident_analytics import router as incident_analytics_router
from app.api.v1.endpoints.dashboard import router as dashboards_router
from app.api.v1.endpoints.notifications import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    setup_logging()

    yield

    # Application shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Affordable AI-powered SRE and observability platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)
# --------------------------------------------------
# Registering EndPoints
# --------------------------------------------------
app.include_router(applications_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(monitors_router, prefix="/api/v1")
app.include_router(log_entries_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(incident_events_router, prefix="/api/v1")
app.include_router(incident_analyses_router, prefix="/api/v1")
app.include_router(incident_services_router, prefix="/api/v1")
app.include_router(service_dependencies_router, prefix="/api/v1")
app.include_router(monitor_checks_router, prefix="/api/v1")
app.include_router(incident_analytics_router, prefix="/api/v1")
app.include_router(dashboards_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
# --------------------------------------------------
# Global Exception Handlers
# --------------------------------------------------
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)
app.add_exception_handler(
    IntegrityError,
    integrity_exception_handler,
)
app.add_exception_handler(
    OperationalError,
    operational_exception_handler,
)
app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)
app.add_exception_handler(
    Exception,
    unexpected_exception_handler,
)
# --------------------------------------------------
# Health Check Endpoints
# --------------------------------------------------
@app.get("/")
async def root():
    return {
        "application": settings.APP_NAME,
        "status": "running",
        "version": settings.APP_VERSION,
    }
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }
@app.get("/health/database")
async def database_health_check():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {
            "database": "connected",
            "status": "healthy",
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "database": "unavailable",
                "status": "unhealthy",
            },
        )