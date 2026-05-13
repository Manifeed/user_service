from __future__ import annotations

from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Header, Path, Query
from sqlalchemy.orm import Session

from app.database import get_identity_read_db_session, get_identity_write_db_session
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

from shared_backend.clients.user_service_networking_client import (
    INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER,
    INTERNAL_CURRENT_USER_EMAIL_HEADER,
    INTERNAL_CURRENT_USER_ID_HEADER,
    INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER,
    INTERNAL_CURRENT_USER_ROLE_HEADER,
    INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER,
)
from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import ApiAccessDisabledError, InactiveUserError
from shared_backend.security.internal_service_auth import require_internal_service_token
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
)
from shared_backend.schemas.auth.auth_schema import UserRole
from shared_backend.schemas.internal.user_service_schema import (
    InternalAccountMeRequest,
    InternalAdminUserUpdateRequest,
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
    payload: Annotated[InternalAccountMeRequest, Body(embed=True)],
    db: Session = Depends(get_identity_read_db_session),
) -> AccountMeRead:
    return read_account_me(
        db,
        current_user=_require_active_user(_current_user_from_payload(payload.current_user)),
    )


@internal_user_router.patch("/account/me", response_model=AccountProfileUpdateRead)
def update_internal_account_me(
    payload: Annotated[InternalAccountProfileUpdateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_write_db_session),
) -> AccountProfileUpdateRead:
    return update_account_profile(
        db,
        payload.payload,
        current_user=_require_active_user(_current_user_from_payload(payload.current_user)),
    )


@internal_user_router.patch("/account/password", response_model=AccountPasswordUpdateRead)
def update_internal_account_password(
    payload: Annotated[InternalAccountPasswordUpdateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_write_db_session),
) -> AccountPasswordUpdateRead:
    return update_account_password(
        db,
        payload.payload,
        current_user=_require_active_user(_current_user_from_payload(payload.current_user)),
    )


@internal_user_router.get("/account/api-keys", response_model=UserApiKeyListRead)
def read_internal_account_api_keys(
    current_user_id: Annotated[int, Header(alias=INTERNAL_CURRENT_USER_ID_HEADER, ge=1)],
    current_user_email: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_EMAIL_HEADER, min_length=3, max_length=320)],
    current_user_role: Annotated[UserRole, Header(alias=INTERNAL_CURRENT_USER_ROLE_HEADER)],
    current_user_is_active: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER)],
    current_user_api_access_enabled: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER)],
    current_user_session_expires_at: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER)],
    db: Session = Depends(get_identity_read_db_session),
) -> UserApiKeyListRead:
    current_user = _read_current_user_from_headers(
        user_id=current_user_id,
        email=current_user_email,
        role=current_user_role,
        is_active=current_user_is_active,
        api_access_enabled=current_user_api_access_enabled,
        session_expires_at=current_user_session_expires_at,
    )
    return read_account_api_keys(
        db,
        current_user=_require_api_enabled_user(current_user),
    )


@internal_user_router.post("/account/api-keys", response_model=UserApiKeyCreateRead)
def create_internal_account_api_key(
    payload: Annotated[InternalApiKeyCreateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_write_db_session),
) -> UserApiKeyCreateRead:
    return create_account_api_key(
        db,
        payload.payload,
        current_user=_require_api_enabled_user(_current_user_from_payload(payload.current_user)),
    )


@internal_user_router.delete("/account/api-keys/{api_key_id}", response_model=UserApiKeyDeleteRead)
def delete_internal_account_api_key(
    current_user_id: Annotated[int, Header(alias=INTERNAL_CURRENT_USER_ID_HEADER, ge=1)],
    current_user_email: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_EMAIL_HEADER, min_length=3, max_length=320)],
    current_user_role: Annotated[UserRole, Header(alias=INTERNAL_CURRENT_USER_ROLE_HEADER)],
    current_user_is_active: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER)],
    current_user_api_access_enabled: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER)],
    current_user_session_expires_at: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER)],
    api_key_id: int = Path(ge=1),
    db: Session = Depends(get_identity_write_db_session),
) -> UserApiKeyDeleteRead:
    current_user = _read_current_user_from_headers(
        user_id=current_user_id,
        email=current_user_email,
        role=current_user_role,
        is_active=current_user_is_active,
        api_access_enabled=current_user_api_access_enabled,
        session_expires_at=current_user_session_expires_at,
    )
    return delete_account_api_key(
        db,
        api_key_id,
        current_user=_require_api_enabled_user(current_user),
    )


@internal_user_router.get("/admin/users", response_model=AdminUserListRead)
def read_internal_admin_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    api_access_enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=320),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user_id: Annotated[int, Header(alias=INTERNAL_CURRENT_USER_ID_HEADER, ge=1)] = 0,
    current_user_email: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_EMAIL_HEADER, min_length=3, max_length=320)] = "",
    current_user_role: Annotated[UserRole, Header(alias=INTERNAL_CURRENT_USER_ROLE_HEADER)] = "user",
    current_user_is_active: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER)] = False,
    current_user_api_access_enabled: Annotated[bool, Header(alias=INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER)] = False,
    current_user_session_expires_at: Annotated[str, Header(alias=INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER)] = "",
    db: Session = Depends(get_identity_read_db_session),
) -> AdminUserListRead:
    current_user = _read_current_user_from_headers(
        user_id=current_user_id,
        email=current_user_email,
        role=current_user_role,
        is_active=current_user_is_active,
        api_access_enabled=current_user_api_access_enabled,
        session_expires_at=current_user_session_expires_at,
    )
    return read_admin_users(
        db,
        current_user=current_user,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
        limit=limit,
        offset=offset,
    )


@internal_user_router.patch("/admin/users/{user_id}", response_model=AdminUserRead)
def update_internal_admin_user(
    payload: Annotated[InternalAdminUserUpdateRequest, Body(embed=True)],
    user_id: int = Path(ge=1),
    db: Session = Depends(get_identity_write_db_session),
) -> AdminUserRead:
    return update_admin_user(
        db,
        user_id,
        payload.payload,
        current_user=_current_user_from_payload(payload.current_user),
    )


def _require_active_user(current_user: AuthenticatedUserContext) -> AuthenticatedUserContext:
    if not current_user.is_active:
        raise InactiveUserError()
    return current_user


def _require_api_enabled_user(current_user: AuthenticatedUserContext) -> AuthenticatedUserContext:
    current_user = _require_active_user(current_user)
    if not current_user.api_access_enabled:
        raise ApiAccessDisabledError()
    return current_user


def _current_user_from_payload(payload: InternalCurrentUserPayload) -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=payload.user_id,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        api_access_enabled=payload.api_access_enabled,
        session_expires_at=payload.session_expires_at,
    )


def _read_current_user_from_headers(
    *,
    user_id: int,
    email: str,
    role: UserRole,
    is_active: bool,
    api_access_enabled: bool,
    session_expires_at: str,
) -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=user_id,
        email=email,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        session_expires_at=datetime.fromisoformat(session_expires_at),
    )
