from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.internal_user_router as router_module

from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import AdminAccessRequiredError
from shared_backend.errors.exception_handlers import register_exception_handlers
from shared_backend.schemas.account.account_schema import AccountMeRead, UserApiKeyListRead
from shared_backend.schemas.admin.admin_user_schema import AdminUserListRead, AdminUserRead
from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead
def _admin_headers(*, role: str = "admin") -> dict[str, str]:
    return {
        router_module.INTERNAL_CURRENT_USER_ID_HEADER: "2",
        router_module.INTERNAL_CURRENT_USER_EMAIL_HEADER: "admin@example.com",
        router_module.INTERNAL_CURRENT_USER_ROLE_HEADER: role,
        router_module.INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER: "true",
        router_module.INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER: "true",
        router_module.INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER: datetime.now(timezone.utc).isoformat(),
    }


def _current_user_headers(*, api_access_enabled: bool = True) -> dict[str, str]:
    return {
        router_module.INTERNAL_CURRENT_USER_ID_HEADER: "1",
        router_module.INTERNAL_CURRENT_USER_EMAIL_HEADER: "user@example.com",
        router_module.INTERNAL_CURRENT_USER_ROLE_HEADER: "user",
        router_module.INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER: "true",
        router_module.INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER: (
            "true" if api_access_enabled else "false"
        ),
        router_module.INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER: datetime.now(timezone.utc).isoformat(),
    }


def _current_user_payload(*, api_access_enabled: bool = True) -> dict[str, object]:
    return {
        "user_id": 1,
        "email": "user@example.com",
        "role": "user",
        "is_active": True,
        "api_access_enabled": api_access_enabled,
        "session_expires_at": datetime.now(timezone.utc).isoformat(),
    }




def _user_read(*, role: str = "user") -> AuthenticatedUserRead:
    now = datetime.now(timezone.utc)
    return AuthenticatedUserRead(
        id=1,
        email="user@example.com",
        pseudo="user",
        pp_id=1,
        role=role,
        is_active=True,
        api_access_enabled=True,
        created_at=now,
        updated_at=now,
    )


def _current_user(*, role: str = "user") -> AuthenticatedUserContext:
    now = datetime.now(timezone.utc)
    return AuthenticatedUserContext(
        user_id=1,
        email="user@example.com",
        role=role,
        is_active=True,
        api_access_enabled=True,
        session_expires_at=now,
    )


def _build_client(monkeypatch) -> TestClient:
    app = FastAPI()
    app.include_router(router_module.internal_user_router)
    register_exception_handlers(app)
    app.dependency_overrides[router_module.require_internal_service_token] = lambda: None
    app.dependency_overrides[router_module.get_identity_db_session] = lambda: object()

    user = _user_read()
    monkeypatch.setattr(
        router_module,
        "read_account_me",
        lambda db, *, current_user: AccountMeRead(user=user),
    )
    monkeypatch.setattr(
        router_module,
        "read_account_api_keys",
        lambda db, *, current_user: UserApiKeyListRead(items=[]),
    )
    monkeypatch.setattr(
        router_module,
        "read_admin_users",
        lambda db, **kwargs: (
            (_ for _ in ()).throw(AdminAccessRequiredError())
            if kwargs["current_user"].role != "admin"
            else AdminUserListRead(items=[], total=0, active_total=0, limit=100, offset=0)
        ),
    )
    monkeypatch.setattr(
        router_module,
        "delete_account_api_key",
        lambda db, api_key_id, *, current_user: type("DeleteResponse", (), {"ok": True})(),
    )
    monkeypatch.setattr(
        router_module,
        "update_admin_user",
        lambda db, user_id, payload, *, current_user: AdminUserRead(
            id=user_id,
            email="user@example.com",
            pseudo="user",
            role="user",
            is_active=payload.is_active if payload.is_active is not None else True,
            api_access_enabled=(
                payload.api_access_enabled if payload.api_access_enabled is not None else True
            ),
        ),
    )
    return TestClient(app)


def test_internal_account_api_key_routes_require_current_user_headers(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    requests = [
        ("GET", "/internal/users/account/api-keys"),
        ("DELETE", "/internal/users/account/api-keys/1"),
    ]

    for method, path in requests:
        response = client.request(method, path)
        assert response.status_code == 422, path


def test_internal_account_api_key_routes_accept_current_user_headers(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    requests = [
        ("GET", "/internal/users/account/api-keys"),
        ("DELETE", "/internal/users/account/api-keys/1"),
    ]

    for method, path in requests:
        response = client.request(method, path, headers=_current_user_headers())
        assert response.status_code == 200, path


def test_internal_account_routes_use_supplied_current_user_without_auth_lookup(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.post(
        "/internal/users/account/me",
        json={"payload": {"current_user": _current_user_payload()}},
    )

    assert response.status_code == 200


def test_internal_admin_routes_reject_non_admin_users(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get(
        "/internal/users/admin/users",
        headers=_admin_headers(role="user"),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "admin_access_required"


def test_internal_admin_routes_accept_wrapped_admin_payloads(monkeypatch) -> None:
    client = _build_client(monkeypatch)
    admin_payload = {
        "current_user": {
            "user_id": 2,
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True,
            "api_access_enabled": True,
            "session_expires_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    list_response = client.get(
        "/internal/users/admin/users?limit=10&offset=0",
        headers=_admin_headers(),
    )
    update_response = client.patch(
        "/internal/users/admin/users/3",
        json={"payload": {**admin_payload, "payload": {"is_active": False}}},
    )

    assert list_response.status_code == 200
    assert update_response.status_code == 200
