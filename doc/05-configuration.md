# Configuration

## Core Runtime

- `APP_ENV`: primary environment selector
- `ENVIRONMENT`: fallback environment selector
- `IDENTITY_DATABASE_URL`: PostgreSQL DSN for identity database
- `REQUIRE_EXPLICIT_DATABASE_URLS`: forces explicit DB URL in strict envs
- `AUTH_SERVICE_URL`: internal base URL for `auth_service`
- `AUTH_SERVICE_TIMEOUT_SECONDS`
	- default: `5`
	- invalid/non-positive values fallback to default in shared service-client helpers
- `INTERNAL_SERVICE_TOKEN`: shared internal secret
- `INTERNAL_SERVICE_TOKENS`: optional comma-separated accepted ingress tokens
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: strict token requirement toggle

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
- `/internal/ready` now depends on `AUTH_SERVICE_URL` being configured because account flows revalidate through `auth_service`
