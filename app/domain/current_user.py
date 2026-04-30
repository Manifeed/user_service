from __future__ import annotations

from app.clients.database.identity_database_client import UserRecord

from shared_backend.domain.current_user import (
    AuthenticatedUserContext,
    build_authenticated_user_read as build_shared_authenticated_user_read,
)
from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead


def build_authenticated_user_read(user: UserRecord) -> AuthenticatedUserRead:
    return build_shared_authenticated_user_read(user)
