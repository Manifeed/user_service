# Security

## Internal Service Authentication

Header used for internal authorization:

- `x-manifeed-internal-token`

Policy:

- local/test-like environments may allow missing token when not configured
- `REQUIRE_INTERNAL_SERVICE_TOKEN=true` forces strict mode even in local-like environments
- strict environments require configured token
- strict environments accept either one `INTERNAL_SERVICE_TOKEN` or a comma-separated `INTERNAL_SERVICE_TOKENS` set
- weak tokens are rejected in strict mode
- token comparison uses constant-time `secrets.compare_digest`
- `/internal/health` and `/internal/ready` stay unauthenticated for orchestration probes

## Account Trust Boundary

Account routes no longer trust caller-supplied user identity.

Current behavior:

- caller sends only `session_token`
- `user_service` resolves that token through `auth_service`
- the returned authenticated context becomes the only source of truth for:
  - `user_id`
  - `role`
  - `is_active`
  - `api_access_enabled`
  - `session_expires_at`

This closes the earlier trust flaw where an internal caller could forge
account identity fields directly.

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
- session-token hashing for API keys uses plain SHA-256 without an extra pepper
