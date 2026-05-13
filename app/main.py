from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import check_identity_database_ready
from app.routers.internal_user_router import internal_user_router

from shared_backend.errors.exception_handlers import register_exception_handlers
from shared_backend.security.internal_service_auth import validate_internal_service_token_configuration
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead
from shared_backend.utils.logging_utils import (
    configure_service_logging,
    create_request_logging_middleware,
)


@asynccontextmanager
async def _app_lifespan(_: FastAPI):
    validate_internal_service_token_configuration()
    yield


def create_app() -> FastAPI:
    configure_service_logging("user-service")
    app = FastAPI(title="Manifeed User Service", lifespan=_app_lifespan)
    app.middleware("http")(
        create_request_logging_middleware(
            service_name="user-service",
            route_class="internal-user",
        )
    )
    app.include_router(internal_user_router)
    register_exception_handlers(app)

    @app.get("/internal/health", response_model=InternalServiceHealthRead)
    def read_internal_health() -> InternalServiceHealthRead:
        return InternalServiceHealthRead(service="user-service", status="ok")

    @app.get("/internal/ready", response_model=InternalServiceHealthRead)
    def read_internal_ready() -> InternalServiceHealthRead:
        validate_internal_service_token_configuration()
        check_identity_database_ready()
        return InternalServiceHealthRead(service="user-service", status="ready")

    return app


app = create_app()
