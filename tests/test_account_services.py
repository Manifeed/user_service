from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.clients.database.identity_database_client import UserApiKeyRecord
from app.services import account_api_key_service, update_account_password
from shared_backend.schemas.account.account_schema import (
    AccountPasswordUpdateRequestSchema,
    UserApiKeyCreateRequestSchema,
)


class _NestedTransaction(AbstractContextManager["_NestedTransaction"]):
    def __init__(self, db: "_FakeSession") -> None:
        self._db = db

    def __enter__(self) -> "_NestedTransaction":
        self._db.begin_nested_calls += 1
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._db.nested_error_count += 1
        return False


class _FakeSession:
    def __init__(self) -> None:
        self.begin_nested_calls = 0
        self.nested_error_count = 0
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0

    def begin_nested(self) -> _NestedTransaction:
        return _NestedTransaction(self)

    def flush(self) -> None:
        self.flush_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


def _current_user() -> SimpleNamespace:
    return SimpleNamespace(
        user_id=1,
        email="user@example.com",
        role="user",
        is_active=True,
        api_access_enabled=True,
        session_expires_at=datetime.now(timezone.utc),
    )


def test_update_account_password_updates_hash_and_revokes_sessions(monkeypatch) -> None:
    db = _FakeSession()
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        update_account_password.identity_database_client,
        "get_user_by_id",
        lambda db, *, user_id: SimpleNamespace(password_hash="current-hash"),
    )
    monkeypatch.setattr(update_account_password, "verify_password", lambda password_hash, password: True)
    monkeypatch.setattr(update_account_password, "validate_password_policy", lambda password: None)
    monkeypatch.setattr(update_account_password, "hash_password", lambda password: "next-hash")
    monkeypatch.setattr(
        update_account_password.identity_database_client,
        "update_user_password_hash",
        lambda db, *, user_id, password_hash: seen.setdefault("password_hash", password_hash),
    )
    monkeypatch.setattr(
        update_account_password.identity_database_client,
        "revoke_user_sessions_by_user_id",
        lambda db, *, user_id: seen.setdefault("revoked_user_id", user_id),
    )

    result = update_account_password.update_account_password(
        db,
        AccountPasswordUpdateRequestSchema(
            current_password="current-password",
            new_password="new-password-123",
        ),
        current_user=_current_user(),
    )

    assert result.ok is True
    assert seen["password_hash"] == "next-hash"
    assert seen["revoked_user_id"] == 1
    assert db.commit_calls == 1
    assert db.rollback_calls == 0


def test_create_account_api_key_retries_with_nested_transaction_without_global_rollback(monkeypatch) -> None:
    db = _FakeSession()
    attempts = {"count": 0}

    monkeypatch.setattr(
        account_api_key_service.identity_database_client,
        "get_user_by_id",
        lambda db, *, user_id: SimpleNamespace(pseudo="user"),
    )
    monkeypatch.setattr(account_api_key_service, "generate_api_key", lambda: "mk_test_key")
    monkeypatch.setattr(account_api_key_service, "build_key_prefix", lambda api_key: "mk_test_pref")
    monkeypatch.setattr(account_api_key_service, "hash_secret_token", lambda api_key: "hashed-token")

    def fake_create_user_api_key(db, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise IntegrityError("insert", {}, Exception("duplicate"))
        return UserApiKeyRecord(
            id=4,
            user_id=1,
            label=kwargs["label"],
            worker_type=kwargs["worker_type"],
            worker_number=2,
            key_prefix=kwargs["key_prefix"],
            last_used_at=None,
            revoked_at=None,
            created_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(
        account_api_key_service.identity_database_client,
        "create_user_api_key",
        fake_create_user_api_key,
    )

    result = account_api_key_service.create_account_api_key(
        db,
        UserApiKeyCreateRequestSchema(label=" smoke ", worker_type="rss_scrapper"),
        current_user=_current_user(),
        commit=False,
    )

    assert result.api_key == "mk_test_key"
    assert result.api_key_info.id == 4
    assert attempts["count"] == 2
    assert db.begin_nested_calls == 2
    assert db.nested_error_count == 1
    assert db.flush_calls == 1
    assert db.commit_calls == 0
    assert db.rollback_calls == 0
