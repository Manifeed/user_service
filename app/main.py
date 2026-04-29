from __future__ import annotations

from fastapi import FastAPI

from app.errors.exception_handlers import register_exception_handlers
from app.schemas.internal.service_schema import InternalServiceHealthRead
from app.routers.internal_user_router import internal_user_router


app = FastAPI(title="Manifeed User Service")
app.include_router(internal_user_router)
register_exception_handlers(app)


@app.get("/internal/health", response_model=InternalServiceHealthRead)
def read_internal_health() -> InternalServiceHealthRead:
    return InternalServiceHealthRead(service="user-service", status="ok")
