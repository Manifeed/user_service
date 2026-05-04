# Operations

## Probes

- `GET /internal/health`
  - liveness only
  - returns `{"service":"user-service","status":"ok"}`

- `GET /internal/ready`
  - readiness check
  - validates token configuration
  - validates DB connectivity
  - validates internal auth client bootstrap

Container healthchecks should use `/internal/ready`, not `/internal/health`.

## Operational Dependencies

Required runtime dependencies:

- identity PostgreSQL database
- reachable `auth_service`
- internal service token configuration in strict environments

If `auth_service` is unavailable, account routes will fail because session
revalidation is now mandatory.

## Logging And Errors

- request logging is emitted through shared logging middleware
- unhandled exceptions are mapped to shared `internal_error` JSON payloads
- expected domain errors keep stable `code`/`message` payloads

## Current Constraints

- admin routes rely on trusted upstream identity payloads rather than direct session revalidation
- account reads and writes are tightly coupled to identity DB availability
- no background tasks run in `user_service`; all work is request-driven

## Recommended Production Hardening

- move from shared header secrets to stronger service-to-service identity
- add end-to-end readiness checks that exercise `auth_service` resolution
- add DB integration coverage for the API-key allocation path
