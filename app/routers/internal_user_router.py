from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_identity_db_session
from app.domain.current_user import AuthenticatedUserContext
from shared_backend.security.internal_service_auth import require_internal_service_token
from app.services.account_api_key_service import (
    create_account_api_key,
    delete_account_api_key,
    read_account_api_keys,
)
from app.services.read_account_me import read_account_me
from app.services.read_admin_users import read_admin_users
from app.services.update_account_password import update_account_password
from app.services.update_account_profile import update_account_profile
from app.services.update_admin_user import update_admin_user

from shared_backend.schemas.account.account_schema import (
    AccountMeRead,
    AccountPasswordUpdateRead,
    AccountProfileUpdateRead,
    UserApiKeyCreateRead,
    UserApiKeyDeleteRead,
    UserApiKeyListRead,
)
from shared_backend.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from shared_backend.schemas.auth.auth_schema import UserRole
from shared_backend.schemas.internal.user_service_schema import (
    InternalAccountPasswordUpdateRequest,
    InternalAccountProfileUpdateRequest,
    InternalApiKeyCreateRequest,
    InternalCurrentUserPayload,
)


internal_user_router = APIRouter(
    prefix="/internal/users",
    tags=["internal-users"],
    dependencies=[Depends(require_internal_service_token)],
)


@internal_user_router.post("/account/me", response_model=AccountMeRead)
def read_internal_account_me(
    payload: InternalCurrentUserPayload,
    db: Session = Depends(get_identity_db_session),
) -> AccountMeRead:
    return read_account_me(
        db,
        current_user=_to_current_user_context(payload),
    )


@internal_user_router.patch("/account/me", response_model=AccountProfileUpdateRead)
def update_internal_account_me(
    request_payload: InternalAccountProfileUpdateRequest,
    db: Session = Depends(get_identity_db_session),
) -> AccountProfileUpdateRead:
    return update_account_profile(
        db,
        request_payload.payload,
        current_user=_to_current_user_context(request_payload.current_user),
    )


@internal_user_router.patch("/account/password", response_model=AccountPasswordUpdateRead)
def update_internal_account_password(
    request_payload: InternalAccountPasswordUpdateRequest,
    db: Session = Depends(get_identity_db_session),
) -> AccountPasswordUpdateRead:
    return update_account_password(
        db,
        request_payload.payload,
        current_user=_to_current_user_context(request_payload.current_user),
    )


@internal_user_router.post("/account/api-keys/list", response_model=UserApiKeyListRead)
def read_internal_account_api_keys(
    payload: InternalCurrentUserPayload,
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyListRead:
    return read_account_api_keys(
        db,
        current_user=_to_current_user_context(payload),
    )


@internal_user_router.post("/account/api-keys", response_model=UserApiKeyCreateRead)
def create_internal_account_api_key(
    request_payload: InternalApiKeyCreateRequest,
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyCreateRead:
    return create_account_api_key(
        db,
        request_payload.payload,
        current_user=_to_current_user_context(request_payload.current_user),
    )


@internal_user_router.post(
    "/account/api-keys/{api_key_id}/delete",
    response_model=UserApiKeyDeleteRead,
)
def delete_internal_account_api_key(
    payload: InternalCurrentUserPayload,
    api_key_id: int = Path(ge=1),
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyDeleteRead:
    return delete_account_api_key(
        db,
        api_key_id,
        current_user=_to_current_user_context(payload),
    )


@internal_user_router.get("/admin/users", response_model=AdminUserListRead)
def read_internal_admin_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    api_access_enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=320),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_identity_db_session),
) -> AdminUserListRead:
    return read_admin_users(
        db,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
        limit=limit,
        offset=offset,
    )


@internal_user_router.patch("/admin/users/{user_id}", response_model=AdminUserRead)
def update_internal_admin_user(
    payload: AdminUserUpdateRequestSchema,
    user_id: int = Path(ge=1),
    db: Session = Depends(get_identity_db_session),
) -> AdminUserRead:
    return update_admin_user(
        db,
        user_id,
        payload,
    )


def _to_current_user_context(payload: InternalCurrentUserPayload) -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=payload.user_id,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        api_access_enabled=payload.api_access_enabled,
        session_expires_at=payload.session_expires_at,
    )
