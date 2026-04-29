from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.database import identity_database_client
from app.domain.user_identity import normalize_user_pseudo
from app.domain.current_user import (
    AuthenticatedUserContext,
    build_authenticated_user_read,
)
from app.errors.app_error import ConflictError
from app.errors.custom_exceptions import InvalidPseudoError, UserNotFoundError
from app.schemas.account.account_schema import (
    AccountProfileUpdateRead,
    AccountProfileUpdateRequestSchema,
)


def update_account_profile(
    db: Session,
    payload: AccountProfileUpdateRequestSchema,
    *,
    current_user: AuthenticatedUserContext,
    commit: bool = True,
) -> AccountProfileUpdateRead:
    existing_user = identity_database_client.get_user_by_id(
        db,
        user_id=current_user.user_id,
    )
    if existing_user is None:
        raise UserNotFoundError()

    normalized_pseudo: str | None = None
    if payload.pseudo is not None:
        normalized_pseudo = normalize_user_pseudo(payload.pseudo)
        if not normalized_pseudo:
            raise InvalidPseudoError()

    try:
        user = identity_database_client.update_user_fields(
            db,
            user_id=current_user.user_id,
            pseudo=normalized_pseudo,
            pp_id=payload.pp_id,
            role=None,
            is_active=None,
            api_access_enabled=None,
        )
        if commit:
            db.commit()
    except IntegrityError as exception:
        if commit:
            db.rollback()
        raise ConflictError(
            "Pseudo already registered",
            code="pseudo_already_registered",
        ) from exception
    except Exception:
        if commit:
            db.rollback()
        raise

    return AccountProfileUpdateRead(user=build_authenticated_user_read(user))
