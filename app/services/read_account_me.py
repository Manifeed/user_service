from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.domain.current_user import (
    AuthenticatedUserContext,
    build_authenticated_user_read,
)
from app.errors.custom_exceptions import UserNotFoundError
from app.schemas.account.account_schema import AccountMeRead


def read_account_me(
    db: Session,
    *,
    current_user: AuthenticatedUserContext,
) -> AccountMeRead:
    user = identity_database_client.get_user_by_id(db, user_id=current_user.user_id)
    if user is None:
        raise UserNotFoundError()

    return AccountMeRead(user=build_authenticated_user_read(user))
