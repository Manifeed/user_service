from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.internal_user_router as router_module

from app.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import InvalidSessionTokenError
from shared_backend.errors.exception_handlers import register_exception_handlers
from shared_backend.schemas.account.account_schema import AccountMeRead, UserApiKeyListRead
from shared_backend.schemas.admin.admin_user_schema import AdminUserListRead, AdminUserRead
from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead


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
        "resolve_authenticated_user_context",
        lambda *, session_token: _current_user(),
    )
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
        lambda db, **kwargs: AdminUserListRead(items=[], total=0, active_total=0, limit=100, offset=0),
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


def test_internal_account_routes_reject_flat_json_bodies(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    requests = [
        ("POST", "/internal/users/account/me", {"session_token": "msess_example"}),
        ("POST", "/internal/users/account/api-keys/list", {"session_token": "msess_example"}),
    ]

    for method, path, body in requests:
        response = client.request(method, path, json=body)
        assert response.status_code == 422, path


def test_internal_account_routes_accept_wrapped_session_payloads(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    requests = [
        ("POST", "/internal/users/account/me", {"payload": {"session_token": "msess_example"}}),
        ("POST", "/internal/users/account/api-keys/list", {"payload": {"session_token": "msess_example"}}),
    ]

    for method, path, body in requests:
        response = client.request(method, path, json=body)
        assert response.status_code == 200, path


def test_internal_account_routes_surface_invalid_session_errors(monkeypatch) -> None:
    client = _build_client(monkeypatch)
    monkeypatch.setattr(
        router_module,
        "resolve_authenticated_user_context",
        lambda *, session_token: (_ for _ in ()).throw(InvalidSessionTokenError()),
    )

    response = client.post(
        "/internal/users/account/me",
        json={"payload": {"session_token": "msess_invalid"}},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session_token"


def test_internal_admin_routes_reject_non_admin_users(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.post(
        "/internal/users/admin/users/list",
        json={
            "payload": {
                "current_user": {
                    "user_id": 1,
                    "email": "user@example.com",
                    "role": "user",
                    "is_active": True,
                    "api_access_enabled": True,
                    "session_expires_at": datetime.now(timezone.utc).isoformat(),
                },
                "filters": {},
            }
        },
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

    list_response = client.post(
        "/internal/users/admin/users/list",
        json={"payload": {**admin_payload, "filters": {"limit": 10, "offset": 0}}},
    )
    update_response = client.patch(
        "/internal/users/admin/users/3",
        json={"payload": {**admin_payload, "payload": {"is_active": False}}},
    )

    assert list_response.status_code == 200
    assert update_response.status_code == 200
