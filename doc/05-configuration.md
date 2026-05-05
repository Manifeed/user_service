# Configuration

## Core Runtime

- `APP_ENV`: primary environment selector
- `ENVIRONMENT`: fallback environment selector
- `IDENTITY_DATABASE_URL`: PostgreSQL DSN for identity database
- `REQUIRE_EXPLICIT_DATABASE_URLS`: forces explicit DB URL in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared internal secret
  - required at startup, minimum 32 characters
- `INTERNAL_SERVICE_TOKENS`: optional comma-separated accepted ingress tokens

## Database Pool Variables

- `DB_POOL_SIZE`
	- default: `20`
	- invalid/too-small values fallback to default

- `DB_MAX_OVERFLOW`
	- default: `40`
	- invalid/negative values fallback to default

- `DB_POOL_TIMEOUT_SECONDS`
	- default: `30`
	- invalid/too-small values fallback to default

- `DB_POOL_RECYCLE_SECONDS`
	- default: `1800`
	- invalid/too-small values fallback to default

## Configuration Notes

- local/test environments may fallback to the built-in local identity DB URL when strict explicit-URL mode is off
- `/internal/ready` validates internal token configuration and identity DB connectivity
- account flows receive a current-user context from `public_api`; `user_service` no longer requires `AUTH_SERVICE_URL`
