from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.services.current_user_context_service import ensure_admin_user
from app.services.read_admin_users import build_admin_user_read

from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import UserNotFoundError
from shared_backend.schemas.admin.admin_user_schema import AdminUserRead, AdminUserUpdateRequestSchema


def update_admin_user(
    db: Session,
    user_id: int,
    payload: AdminUserUpdateRequestSchema,
    *,
    current_user: AuthenticatedUserContext,
    commit: bool = True,
) -> AdminUserRead:
    ensure_admin_user(current_user)
    existing_user = identity_database_client.get_user_by_id(db, user_id=user_id)
    if existing_user is None:
        raise UserNotFoundError()

    try:
        user = identity_database_client.update_user_fields(
            db,
            user_id=user_id,
            pseudo=None,
            pp_id=None,
            role=None,
            is_active=payload.is_active,
            api_access_enabled=payload.api_access_enabled,
        )
        if commit:
            db.commit()
    except Exception:
        if commit:
            db.rollback()
        raise

    return build_admin_user_read(user)
