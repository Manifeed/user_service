# Security

## Internal Service Authentication

Header used for internal authorization:

- `x-manifeed-internal-token`

Policy:

- the service fails startup when no token is configured
- accepted tokens come from `INTERNAL_SERVICE_TOKEN` or comma-separated `INTERNAL_SERVICE_TOKENS`
- weak tokens are rejected
- token comparison uses constant-time `secrets.compare_digest`
- `/internal/health` and `/internal/ready` stay unauthenticated for orchestration probes

## Account Trust Boundary

Account routes trust only service-authenticated callers and the current-user
context produced by `public_api` after session resolution.

Current behavior:

- `public_api` resolves the browser session through `auth_service`
- caller sends internal token plus the resolved authenticated context
- the authenticated context becomes the source of truth for:
  - `user_id`
  - `role`
  - `is_active`
  - `api_access_enabled`
  - `session_expires_at`

This removes the duplicated `user_service -> auth_service` lookup on account
routes while keeping the public session proof at the gateway boundary.

## Admin Trust Boundary

Admin routes require a `current_user` payload and revalidate that the role is
`admin` inside `user_service`.

Important nuance:

- admin flows do not currently re-resolve a session through `auth_service`
- they still trust upstream internal callers to originate the correct admin identity
- the local admin role check is defense in depth, not a full session proof

## Credential And Secret Handling

- password hashing and verification are delegated to shared backend auth utilities
- only password hashes are stored
- user API keys are stored as:
  - SHA-256 hash
  - visible prefix
  - metadata
- clear API key values are returned only at creation time

## Transaction Safety

- API key creation retries use nested transactions
- retryable insert collisions do not rollback unrelated transaction state
- public mutating services own the commit/rollback boundary

## Current Security Gaps

- inter-service auth still uses shared header secrets rather than mTLS or signed service identity
- admin routes still trust upstream caller identity payloads rather than resolving a session directly
- API-key hashing uses plain SHA-256 without an extra pepper
