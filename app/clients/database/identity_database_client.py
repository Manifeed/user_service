from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class UserRecord:
    id: int
    email: str
    pseudo: str
    pp_id: int
    password_hash: str
    role: str
    is_active: bool
    api_access_enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserApiKeyRecord:
    id: int
    user_id: int
    label: str
    worker_type: str
    worker_number: int
    key_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


def get_user_by_id(db: Session, *, user_id: int) -> UserRecord | None:
    row = (
        db.execute(
            text(  # nosec
                """
                SELECT
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return _map_user(row)


def update_user_password_hash(
    db: Session,
    *,
    user_id: int,
    password_hash: str,
) -> UserRecord:
    row = (
        db.execute(
            text(
                """
                UPDATE users
                SET
                    password_hash = :password_hash,
                    updated_at = now()
                WHERE id = :user_id
                RETURNING
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                """
            ),
            {
                "user_id": user_id,
                "password_hash": password_hash,
            },
        )
        .mappings()
        .one()
    )
    return _map_user(row)


def list_users(
    db: Session,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    api_access_enabled: bool | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[UserRecord], int]:
    where_sql, params = _build_user_filters(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    total = count_users(
        db,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    if total == 0:
        return [], 0

    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                FROM users
                {where_sql}
                ORDER BY created_at ASC, id ASC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                **params,
                "limit": max(1, min(int(limit), 100)),
                "offset": max(0, int(offset)),
            },
        )
        .mappings()
        .all()
    )
    return [_map_user(row) for row in rows], total


def count_users(
    db: Session,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    api_access_enabled: bool | None = None,
    search: str | None = None,
) -> int:
    where_sql, params = _build_user_filters(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    return int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM users
                {where_sql}
                """
            ),
            params,
        ).scalar_one()
        or 0
    )


def _build_user_filters(
    *,
    role: str | None,
    is_active: bool | None,
    api_access_enabled: bool | None,
    search: str | None,
) -> tuple[str, dict[str, object]]:
    where_clauses: list[str] = []
    params: dict[str, object] = {}

    if role is not None:
        where_clauses.append("role = :role")
        params["role"] = role
    if is_active is not None:
        where_clauses.append("is_active = :is_active")
        params["is_active"] = is_active
    if api_access_enabled is not None:
        where_clauses.append("api_access_enabled = :api_access_enabled")
        params["api_access_enabled"] = api_access_enabled
    if search is not None:
        normalized_search = search.strip()
        if normalized_search:
            where_clauses.append("(email ILIKE :search OR pseudo ILIKE :search)")
            params["search"] = f"%{normalized_search}%"

    if not where_clauses:
        return "", {}
    return f"WHERE {' AND '.join(where_clauses)}", params


def update_user_fields(
    db: Session,
    *,
    user_id: int,
    pseudo: str | None,
    pp_id: int | None,
    role: str | None,
    is_active: bool | None,
    api_access_enabled: bool | None,
) -> UserRecord:
    set_clauses: list[str] = ["updated_at = now()"]
    params: dict[str, object] = {"user_id": user_id}

    if pseudo is not None:
        set_clauses.append("pseudo = :pseudo")
        params["pseudo"] = pseudo
    if pp_id is not None:
        set_clauses.append("pp_id = :pp_id")
        params["pp_id"] = pp_id
    if role is not None:
        set_clauses.append("role = :role")
        params["role"] = role
    if is_active is not None:
        set_clauses.append("is_active = :is_active")
        params["is_active"] = is_active
    if api_access_enabled is not None:
        set_clauses.append("api_access_enabled = :api_access_enabled")
        params["api_access_enabled"] = api_access_enabled

    row = (
        db.execute(
            text(
                f"""
                UPDATE users
                SET
                    {", ".join(set_clauses)}
                WHERE id = :user_id
                RETURNING
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                """
            ),
            params,
        )
        .mappings()
        .one()
    )
    return _map_user(row)


def revoke_user_sessions_by_user_id(db: Session, *, user_id: int) -> None:
    db.execute(
        text(
            """
            UPDATE user_sessions
            SET revoked_at = now()
            WHERE user_id = :user_id
                AND revoked_at IS NULL
            """
        ),
        {"user_id": user_id},
    )


def list_user_api_keys(db: Session, *, user_id: int) -> list[UserApiKeyRecord]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    label,
                    worker_type,
                    worker_number,
                    key_prefix,
                    last_used_at,
                    revoked_at,
                    created_at
                FROM user_api_keys
                WHERE user_id = :user_id
                    AND revoked_at IS NULL
                ORDER BY created_at DESC, id DESC
                """
            ),
            {"user_id": user_id},
        )
        .mappings()
        .all()
    )
    return [_map_user_api_key(row) for row in rows]


def create_user_api_key(
    db: Session,
    *,
    user_id: int,
    label: str,
    worker_type: str,
    key_prefix: str,
    key_hash: str,
) -> UserApiKeyRecord:
    row = (
        db.execute(
            text(
                """
                INSERT INTO user_api_keys (
                    user_id,
                    label,
                    worker_type,
                    worker_number,
                    key_prefix,
                    key_hash
                )
                SELECT
                    :user_id,
                    :label,
                    CAST(:worker_type AS VARCHAR(64)),
                    COALESCE(MAX(existing.worker_number), 0) + 1,
                    :key_prefix,
                    :key_hash
                FROM user_api_keys AS existing
                WHERE existing.user_id = :user_id
                    AND existing.worker_type = CAST(:worker_type AS VARCHAR(64))
                RETURNING
                    id,
                    user_id,
                    label,
                    worker_type,
                    worker_number,
                    key_prefix,
                    last_used_at,
                    revoked_at,
                    created_at
                """
            ),
            {
                "user_id": user_id,
                "label": label,
                "worker_type": worker_type,
                "key_prefix": key_prefix,
                "key_hash": key_hash,
            },
        )
        .mappings()
        .one()
    )
    return _map_user_api_key(row)


def revoke_user_api_key(
    db: Session,
    *,
    user_id: int,
    api_key_id: int,
) -> bool:
    deleted = db.execute(
        text(
            """
            UPDATE user_api_keys
            SET revoked_at = now()
            WHERE id = :api_key_id
                AND user_id = :user_id
                AND revoked_at IS NULL
            """
        ),
        {
            "user_id": user_id,
            "api_key_id": api_key_id,
        },
    )
    return deleted.rowcount > 0


def _map_user(row) -> UserRecord:
    return UserRecord(
        id=int(row["id"]),
        email=str(row["email"]),
        pseudo=str(row["pseudo"]),
        pp_id=int(row["pp_id"]),
        password_hash=str(row["password_hash"]),
        role=str(row["role"]),
        is_active=bool(row["is_active"]),
        api_access_enabled=bool(row["api_access_enabled"]),
        created_at=_normalize_datetime(row["created_at"]) or datetime.now(timezone.utc),
        updated_at=_normalize_datetime(row["updated_at"]) or datetime.now(timezone.utc),
    )


def _map_user_api_key(row) -> UserApiKeyRecord:
    return UserApiKeyRecord(
        id=int(row["id"]),
        user_id=int(row["user_id"]),
        label=str(row["label"]),
        worker_type=str(row["worker_type"]),
        worker_number=int(row["worker_number"]),
        key_prefix=str(row["key_prefix"]),
        last_used_at=_normalize_datetime(row["last_used_at"]),
        revoked_at=_normalize_datetime(row["revoked_at"]),
        created_at=_normalize_datetime(row["created_at"]) or datetime.now(timezone.utc),
    )


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
