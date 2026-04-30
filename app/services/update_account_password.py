from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.domain.password_policy import validate_password_policy
from app.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import InvalidCredentialsError, UserNotFoundError
from app.utils.auth_utils import hash_password, verify_password

from shared_backend.schemas.account.account_schema import (
    AccountPasswordUpdateRead,
    AccountPasswordUpdateRequestSchema,
)


def update_account_password(
    db: Session,
    payload: AccountPasswordUpdateRequestSchema,
    *,
    current_user: AuthenticatedUserContext,
    commit: bool = True,
) -> AccountPasswordUpdateRead:
    user = identity_database_client.get_user_by_id(db, user_id=current_user.user_id)
    if user is None:
        raise UserNotFoundError()
    if not verify_password(user.password_hash, payload.current_password):
        raise InvalidCredentialsError(
            "Current password is invalid",
            code="invalid_current_password",
        )
    validate_password_policy(payload.new_password)

    try:
        identity_database_client.update_user_password_hash(
            db,
            user_id=current_user.user_id,
            password_hash=hash_password(payload.new_password),
        )
        identity_database_client.revoke_user_sessions_by_user_id(
            db,
            user_id=current_user.user_id,
        )
        if commit:
            db.commit()
    except Exception:
        if commit:
            db.rollback()
        raise

    return AccountPasswordUpdateRead(ok=True)
