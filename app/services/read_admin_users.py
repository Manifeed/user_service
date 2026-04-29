from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database.identity_database_client import UserRecord
from app.clients.database import identity_database_client
from app.schemas.admin.admin_user_schema import AdminUserListRead, AdminUserRead
from app.schemas.auth.auth_schema import UserRole


def read_admin_users(
    db: Session,
    *,
    role: UserRole | None = None,
    is_active: bool | None = None,
    api_access_enabled: bool | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> AdminUserListRead:
    normalized_search = search.strip() if search is not None else None
    effective_search = normalized_search or None
    effective_is_active = is_active
    if effective_is_active is None and effective_search is None:
        effective_is_active = True

    items, total = identity_database_client.list_users(
        db,
        role=role,
        is_active=effective_is_active,
        api_access_enabled=api_access_enabled,
        search=effective_search,
        limit=limit,
        offset=offset,
    )
    return AdminUserListRead(
        items=[build_admin_user_read(user) for user in items],
        total=total,
        active_total=identity_database_client.count_users(db, is_active=True),
        limit=limit,
        offset=offset,
    )


def build_admin_user_read(user: UserRecord) -> AdminUserRead:
    return AdminUserRead(
        id=user.id,
        email=user.email,
        pseudo=user.pseudo,
        role=user.role,
        is_active=user.is_active,
        api_access_enabled=user.api_access_enabled,
    )
