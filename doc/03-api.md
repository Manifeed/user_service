# API Reference

## General Contract

- `GET /internal/health` and `GET /internal/ready` are probe endpoints and do not require the internal auth header
- all `/internal/users/*` business routes require `x-manifeed-internal-token`
- all body-carrying requests use a JSON envelope under `payload`
- validation failures return HTTP `422` with shared `validation_error` payloads
- domain errors return shared JSON payloads with stable `code` and `message` fields

## Health Endpoints

### `GET /internal/health`

Liveness endpoint.

Response:

```json
{
	"service": "user-service",
	"status": "ok"
}
```

### `GET /internal/ready`

Readiness endpoint.

Validates:

- internal token configuration
- identity database connectivity (`SELECT 1`)
- presence of `AUTH_SERVICE_URL` through the internal auth client bootstrap

Response:

```json
{
	"service": "user-service",
	"status": "ready"
}
```

## Account Endpoints

All account endpoints are under `/internal/users/account`.

### `POST /internal/users/account/me`

Reads the authenticated account.

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

Behavior:

- resolves session via `auth_service`
- reloads user from identity DB by `user_id`
- returns shared authenticated user projection

Common error codes:

- `missing_session_token`
- `invalid_session_token`
- `expired_session_token`
- `inactive_user`
- `user_not_found`

### `PATCH /internal/users/account/me`

Updates mutable account profile fields.

Request:

```json
{
	"payload": {
		"session_token": "msess_example",
		"payload": {
			"pseudo": "new-pseudo",
			"pp_id": 2
		}
	}
}
```

Behavior:

- resolves session via `auth_service`
- normalizes pseudo if present
- rejects empty/invalid pseudo values
- rejects duplicate pseudo conflicts

Common error codes:

- `invalid_pseudo`
- `pseudo_already_registered`
- session-related errors listed above

### `PATCH /internal/users/account/password`

Changes password for the authenticated user.

Request:

```json
{
	"payload": {
		"session_token": "msess_example",
		"payload": {
			"current_password": "current-password",
			"new_password": "new-super-secure-password"
		}
	}
}
```

Behavior:

- resolves session via `auth_service`
- verifies current password hash
- validates password policy
- updates password hash
- revokes active sessions for that user

Common error codes:

- `invalid_current_password`
- `weak_password`
- session-related errors listed above

### `POST /internal/users/account/api-keys/list`

Lists active non-revoked API keys for the authenticated user.

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

### `POST /internal/users/account/api-keys`

Creates a new user API key.

Request:

```json
{
	"payload": {
		"session_token": "msess_example",
		"payload": {
			"label": "desktop-worker",
			"worker_type": "rss_scrapper"
		}
	}
}
```

Behavior:

- resolves session via `auth_service`
- requires `api_access_enabled == true`
- allocates next worker number per user/worker type
- retries retryable integrity conflicts with nested transactions
- returns clear API key once plus metadata projection

Common error codes:

- `api_access_disabled`
- `api_key_allocation_failed`
- session-related errors listed above

### `POST /internal/users/account/api-keys/{api_key_id}/delete`

Revokes one active API key for the authenticated user.

Request:

```json
{
	"payload": {
		"session_token": "msess_example"
	}
}
```

Response:

```json
{
	"ok": true
}
```

## Admin Endpoints

All admin endpoints are under `/internal/users/admin/users`.

### `POST /internal/users/admin/users/list`

Lists users for admin tooling.

Request:

```json
{
	"payload": {
		"current_user": {
			"user_id": 2,
			"email": "admin@example.com",
			"role": "admin",
			"is_active": true,
			"api_access_enabled": true,
			"session_expires_at": "2026-05-04T12:00:00Z"
		},
		"filters": {
			"role": "user",
			"is_active": true,
			"api_access_enabled": false,
			"search": "alice",
			"limit": 50,
			"offset": 0
		}
	}
}
```

Behavior:

- rechecks `current_user.role == "admin"`
- defaults to `is_active=true` when no explicit `is_active` and no search are supplied
- returns `active_total` as a separate count

Common error code:

- `admin_access_required`

### `PATCH /internal/users/admin/users/{user_id}`

Updates admin-managed flags on a target user.

Request:

```json
{
	"payload": {
		"current_user": {
			"user_id": 2,
			"email": "admin@example.com",
			"role": "admin",
			"is_active": true,
			"api_access_enabled": true,
			"session_expires_at": "2026-05-04T12:00:00Z"
		},
		"payload": {
			"is_active": false
		}
	}
}
```

Behavior:

- rejects empty update payloads
- updates `is_active` and/or `api_access_enabled`
- does not mutate role or profile fields

Common error codes:

- `admin_access_required`
- `user_not_found`

## Runtime Flows

### Account Read Flow

1. validate internal token
2. validate wrapped session-token payload
3. resolve session through `auth_service`
4. load user by resolved `user_id`
5. return account projection

### Account Password Change Flow

1. validate internal token
2. resolve session through `auth_service`
3. verify current password
4. validate new password policy
5. update password hash
6. revoke active sessions for the user
7. commit transaction

### Admin Update Flow

1. validate internal token
2. validate wrapped `current_user` + update payload
3. enforce admin role locally
4. load target user
5. update allowed admin flags
6. commit transaction
