# Architecture

## High-Level Layers

- `app/main.py`
  - application bootstrap
  - request logging middleware
  - health/readiness endpoints
  - shared exception handler registration

- `app/routers/internal_user_router.py`
  - HTTP-only layer for `/internal/users/*`
  - request body validation
  - DB session injection
  - account session resolution

- `app/services/*`
  - transport-agnostic business logic
  - account read/update/password/API-key use cases
  - admin listing/update use cases

- `app/services/current_user_context_service.py`
  - resolves `session_token` through `auth_service`
  - enforces local admin role checks

- `app/clients/database/identity_database_client.py`
  - SQL access layer
  - user lookup/update
  - API key listing/insert/revocation

- `app/clients/networking/auth_service_networking_client.py`
  - internal HTTP client to `auth_service`
  - currently used for `resolve-session`

## Runtime Collaboration

### Account flows

1. caller sends internal token + wrapped `payload.session_token`
2. router resolves the session via `auth_service`
3. service layer uses the resolved `AuthenticatedUserContext`
4. DB client reads or mutates identity data
5. router returns shared response schemas

### Admin flows

1. caller sends internal token + wrapped `payload.current_user`
2. router passes the request to admin services
3. service layer rechecks `current_user.role == "admin"`
4. DB client reads or mutates target users
5. router returns shared admin response schemas

## Transaction Strategy

- public mutating services use one commit point
- rollback stays at the public service level
- API key creation retries use `db.begin_nested()` so retryable collisions do
  not rollback unrelated outer transaction state
