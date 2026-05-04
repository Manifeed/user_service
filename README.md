# Manifeed User Service

`user_service` is the internal account and user administration service for
Manifeed. It exposes backend-only FastAPI endpoints for authenticated account
reads and updates, user API key management, and admin user listing/mutation.

It is designed for trusted internal consumers, not for browsers or public
clients directly.

## What This Service Provides

- Read the authenticated account profile from the identity database
- Update account profile fields (`pseudo`, `pp_id`)
- Change account password and revoke active sessions afterward
- List, create, and revoke per-user API keys
- List users for admin backoffice workflows
- Update admin-managed flags (`is_active`, `api_access_enabled`)
- Revalidate account flows end-to-end through `auth_service`
- Enforce internal token gate (`x-manifeed-internal-token`) on all user routes
- Expose health and readiness probes for orchestration

## Architecture Overview

- `app/routers`: HTTP route layer under `/internal/users/*`
- `app/services`: transport-agnostic business use cases
- `app/services/current_user_context_service.py`: session resolution and admin guard helpers
- `app/clients/database`: SQLAlchemy session and SQL access layer
- `app/clients/networking/auth_service_networking_client.py`: internal `auth_service` client
- `shared_backend.security.internal_service_auth`: shared inter-service token validation helpers
- `shared_backend.errors.exception_handlers`: shared JSON error mapping
- `shared_backend.utils.logging_utils`: shared request logging middleware

## Quick Start (Local Development)

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Set minimal local environment

```bash
export APP_ENV=local
export IDENTITY_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_identity
export AUTH_SERVICE_URL=http://localhost:8001
```

### 3) Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Service endpoints:

- `GET /internal/health`
- `GET /internal/ready`
- `POST /internal/users/account/me`
- `PATCH /internal/users/account/me`
- `PATCH /internal/users/account/password`
- `POST /internal/users/account/api-keys/list`
- `POST /internal/users/account/api-keys`
- `POST /internal/users/account/api-keys/{api_key_id}/delete`
- `POST /internal/users/admin/users/list`
- `PATCH /internal/users/admin/users/{user_id}`

All internal user endpoints use a JSON body wrapped under `payload`. Account
flows now carry a `session_token` and are revalidated against `auth_service`
before reading or mutating account state.

Example:

```json
{
  "payload": {
    "session_token": "msess_example"
  }
}
```

## Security Model

- All `/internal/users/*` routes require `x-manifeed-internal-token` except in
  explicit local/test environments without configured token.
- Incoming internal auth can validate either one `INTERNAL_SERVICE_TOKEN` or
  multiple accepted secrets via `INTERNAL_SERVICE_TOKENS`.
- Account endpoints no longer trust caller-supplied user context. They resolve
  the session token through `auth_service /internal/auth/resolve-session`.
- Admin endpoints require an explicit `current_user` payload and recheck that
  `role == "admin"` inside `user_service`.
- `/internal/health` and `/internal/ready` stay unauthenticated for probes;
  `/internal/ready` still validates strict token configuration.
- Password hashing and verification are delegated to shared backend auth
  utilities (Argon2-based).
- API keys are stored as hash + visible prefix only; clear API key material is
  returned once at creation time.
- API key allocation retries use nested transactions so retryable collisions do
  not rollback an outer transaction.

## Configuration

### Core runtime

- `APP_ENV` / `ENVIRONMENT`: environment mode resolver
- `IDENTITY_DATABASE_URL`: identity Postgres DSN
- `REQUIRE_EXPLICIT_DATABASE_URLS`: requires explicit DB URL in strict envs
- `AUTH_SERVICE_URL`: internal base URL for `auth_service`
- `AUTH_SERVICE_TIMEOUT_SECONDS`: timeout for session revalidation calls
- `INTERNAL_SERVICE_TOKEN`: shared secret for internal route protection
- `INTERNAL_SERVICE_TOKENS`: optional comma-separated accepted ingress tokens
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: force strict internal token mode

### DB pool tuning

- `DB_POOL_SIZE`: SQLAlchemy pool size (`20`)
- `DB_MAX_OVERFLOW`: SQLAlchemy max overflow (`40`)
- `DB_POOL_TIMEOUT_SECONDS`: pool checkout timeout (`30`)
- `DB_POOL_RECYCLE_SECONDS`: pool recycle interval (`1800`)

## Tests

Run the test suite:

```bash
pytest -q
```

Current tests cover:

- Source syntax validity
- Wrapped `payload` request contract on internal user routes
- Invalid session handling on account routes
- Admin role enforcement on admin routes
- Session-token payload contract in `public_api -> user_service`
- Current-user payload contract in `public_api/admin_service -> user_service`
- Password update side effects
- Nested transaction behavior for API key creation retries

Current gaps before strong production confidence:

- No real DB integration tests for account/profile/password/API-key flows
- No end-to-end contract test that exercises `public_api -> user_service -> auth_service` with real containers in CI

## Docker

Build:

```bash
docker build -t manifeed-user-service -f user_service/Dockerfile ..
```

Run:

```bash
docker run --rm -p 8000:8000 \
	-e APP_ENV=production \
	-e IDENTITY_DATABASE_URL='postgresql://user:pass@host:5432/db' \
	-e AUTH_SERVICE_URL='http://auth-service:8000' \
	-e INTERNAL_SERVICE_TOKEN='replace-with-strong-secret-min-32-chars' \
	manifeed-user-service
```

The image is multi-stage, runs as a non-root user, and installs
`shared_backend` from a wheel built locally from the monorepo. The runtime
base image is `python:3.13-slim`.

## Detailed Documentation

Documentation is available in:

- `doc/README.md`
