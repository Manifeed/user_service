from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_identity_db_session
from shared_backend.security.internal_service_auth import require_internal_service_token
from app.services.account_api_key_service import (
    create_account_api_key,
    delete_account_api_key,
    read_account_api_keys,
)
from app.services.current_user_context_service import resolve_authenticated_user_context
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
)
from shared_backend.schemas.internal.user_service_schema import (
    InternalAdminUserListRequest,
    InternalAdminUserUpdateRequest,
    InternalAccountPasswordUpdateRequest,
    InternalAccountProfileUpdateRequest,
    InternalApiKeyCreateRequest,
    InternalSessionTokenRequest,
)


internal_user_router = APIRouter(
    prefix="/internal/users",
    tags=["internal-users"],
    dependencies=[Depends(require_internal_service_token)],
)


@internal_user_router.post("/account/me", response_model=AccountMeRead)
def read_internal_account_me(
    payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> AccountMeRead:
    return read_account_me(
        db,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.patch("/account/me", response_model=AccountProfileUpdateRead)
def update_internal_account_me(
    payload: Annotated[InternalAccountProfileUpdateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> AccountProfileUpdateRead:
    return update_account_profile(
        db,
        payload.payload,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.patch("/account/password", response_model=AccountPasswordUpdateRead)
def update_internal_account_password(
    payload: Annotated[InternalAccountPasswordUpdateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> AccountPasswordUpdateRead:
    return update_account_password(
        db,
        payload.payload,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.post("/account/api-keys/list", response_model=UserApiKeyListRead)
def read_internal_account_api_keys(
    payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyListRead:
    return read_account_api_keys(
        db,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.post("/account/api-keys", response_model=UserApiKeyCreateRead)
def create_internal_account_api_key(
    payload: Annotated[InternalApiKeyCreateRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyCreateRead:
    return create_account_api_key(
        db,
        payload.payload,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.post(
    "/account/api-keys/{api_key_id}/delete",
    response_model=UserApiKeyDeleteRead,
)
def delete_internal_account_api_key(
    payload: Annotated[InternalSessionTokenRequest, Body(embed=True)],
    api_key_id: int = Path(ge=1),
    db: Session = Depends(get_identity_db_session),
) -> UserApiKeyDeleteRead:
    return delete_account_api_key(
        db,
        api_key_id,
        current_user=resolve_authenticated_user_context(session_token=payload.session_token),
    )


@internal_user_router.post("/admin/users/list", response_model=AdminUserListRead)
def read_internal_admin_users(
    payload: Annotated[InternalAdminUserListRequest, Body(embed=True)],
    db: Session = Depends(get_identity_db_session),
) -> AdminUserListRead:
    return read_admin_users(
        db,
        current_user=payload.current_user,
        role=payload.filters.role,
        is_active=payload.filters.is_active,
        api_access_enabled=payload.filters.api_access_enabled,
        search=payload.filters.search,
        limit=payload.filters.limit,
        offset=payload.filters.offset,
    )


@internal_user_router.patch("/admin/users/{user_id}", response_model=AdminUserRead)
def update_internal_admin_user(
    payload: Annotated[InternalAdminUserUpdateRequest, Body(embed=True)],
    user_id: int = Path(ge=1),
    db: Session = Depends(get_identity_db_session),
) -> AdminUserRead:
    return update_admin_user(
        db,
        user_id,
        payload.payload,
        current_user=payload.current_user,
    )
