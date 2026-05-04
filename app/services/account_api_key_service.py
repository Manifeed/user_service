from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.database.identity_database_client import UserApiKeyRecord
from app.clients.database import identity_database_client
from app.domain.current_user import AuthenticatedUserContext
from shared_backend.domain.worker_identity import build_worker_name
from shared_backend.errors.custom_exceptions import (
    ApiAccessDisabledError,
    ApiKeyAllocationError,
    ApiKeyNotFoundError,
    UserNotFoundError,
)
from app.utils.auth_utils import (
    build_key_prefix,
    generate_api_key,
    hash_secret_token,
)

from shared_backend.schemas.account.account_schema import (
    UserApiKeyCreateRead,
    UserApiKeyCreateRequestSchema,
    UserApiKeyDeleteRead,
    UserApiKeyListRead,
    UserApiKeyRead,
)

MAX_API_KEY_CREATION_RETRIES = 3


def read_account_api_keys(
    db: Session,
    *,
    current_user: AuthenticatedUserContext,
) -> UserApiKeyListRead:
    user = identity_database_client.get_user_by_id(db, user_id=current_user.user_id)
    if user is None:
        raise UserNotFoundError()
    return UserApiKeyListRead(
        items=[
            _build_user_api_key_read(item, pseudo=user.pseudo)
            for item in identity_database_client.list_user_api_keys(
                db,
                user_id=current_user.user_id,
            )
        ]
    )


def create_account_api_key(
    db: Session,
    payload: UserApiKeyCreateRequestSchema,
    *,
    current_user: AuthenticatedUserContext,
    commit: bool = True,
) -> UserApiKeyCreateRead:
    if not current_user.api_access_enabled:
        raise ApiAccessDisabledError()

    user = identity_database_client.get_user_by_id(db, user_id=current_user.user_id)
    if user is None:
        raise UserNotFoundError()

    api_key = generate_api_key()
    normalized_label = payload.label.strip()
    api_key_record = None
    for _ in range(MAX_API_KEY_CREATION_RETRIES):
        try:
            with db.begin_nested():
                api_key_record = identity_database_client.create_user_api_key(
                    db,
                    user_id=current_user.user_id,
                    label=normalized_label,
                    worker_type=payload.worker_type,
                    key_prefix=build_key_prefix(api_key),
                    key_hash=hash_secret_token(api_key),
                )
                db.flush()
                break
        except IntegrityError:
            continue
        except Exception:
            if commit:
                db.rollback()
            raise

    if api_key_record is None:
        if commit:
            db.rollback()
        raise ApiKeyAllocationError()

    if commit:
        db.commit()

    return UserApiKeyCreateRead(
        api_key=api_key,
        api_key_info=_build_user_api_key_read(api_key_record, pseudo=user.pseudo),
    )


def delete_account_api_key(
    db: Session,
    api_key_id: int,
    *,
    current_user: AuthenticatedUserContext,
    commit: bool = True,
) -> UserApiKeyDeleteRead:
    try:
        deleted = identity_database_client.revoke_user_api_key(
            db,
            user_id=current_user.user_id,
            api_key_id=api_key_id,
        )
        if not deleted:
            if commit:
                db.rollback()
            raise ApiKeyNotFoundError()
        if commit:
            db.commit()
    except Exception:
        if commit:
            db.rollback()
        raise

    return UserApiKeyDeleteRead(ok=True)


def _build_user_api_key_read(record: UserApiKeyRecord, *, pseudo: str) -> UserApiKeyRead:
    return UserApiKeyRead(
        id=record.id,
        label=record.label,
        worker_type=record.worker_type,
        worker_name=build_worker_name(
            pseudo=pseudo,
            worker_type=record.worker_type,
            worker_number=record.worker_number,
        ),
        key_prefix=record.key_prefix,
        last_used_at=record.last_used_at,
        created_at=record.created_at,
    )
