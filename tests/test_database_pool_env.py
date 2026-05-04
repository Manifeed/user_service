import importlib

from app import database as database_module


def test_invalid_db_pool_values_fallback_to_defaults(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv(
        "IDENTITY_DATABASE_URL",
        "postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_test",
    )
    monkeypatch.setenv("DB_POOL_SIZE", "not-a-number")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "-1")
    monkeypatch.setenv("DB_POOL_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("DB_POOL_RECYCLE_SECONDS", "")

    module = importlib.reload(database_module)

    assert module.DB_POOL_SIZE == module.DEFAULT_DB_POOL_SIZE
    assert module.DB_MAX_OVERFLOW == module.DEFAULT_DB_MAX_OVERFLOW
    assert module.DB_POOL_TIMEOUT_SECONDS == module.DEFAULT_DB_POOL_TIMEOUT_SECONDS
    assert module.DB_POOL_RECYCLE_SECONDS == module.DEFAULT_DB_POOL_RECYCLE_SECONDS


def test_valid_db_pool_values_are_preserved(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv(
        "IDENTITY_DATABASE_URL",
        "postgresql://manifeed:manifeed@localhost:5432/manifeed_identity_test",
    )
    monkeypatch.setenv("DB_POOL_SIZE", "12")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "24")
    monkeypatch.setenv("DB_POOL_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("DB_POOL_RECYCLE_SECONDS", "900")

    module = importlib.reload(database_module)

    assert module.DB_POOL_SIZE == 12
    assert module.DB_MAX_OVERFLOW == 24
    assert module.DB_POOL_TIMEOUT_SECONDS == 45
    assert module.DB_POOL_RECYCLE_SECONDS == 900
