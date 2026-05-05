# Operations

## Probes

- `GET /internal/health`
  - liveness only
  - returns `{"service":"user-service","status":"ok"}`

- `GET /internal/ready`
  - readiness check
  - validates token configuration
  - validates DB connectivity

Container healthchecks should use `/internal/ready`, not `/internal/health`.

## Operational Dependencies

Required runtime dependencies:

- identity PostgreSQL database
- internal service token configuration

`public_api` performs session resolution before calling account routes, so
`user_service` does not need direct `auth_service` reachability for account
traffic.

## Logging And Errors

- request logging is emitted through shared logging middleware
- unhandled exceptions are mapped to shared `internal_error` JSON payloads
- expected domain errors keep stable `code`/`message` payloads

## Current Constraints

- admin and account routes rely on trusted upstream identity payloads from service-authenticated callers
- account reads and writes are tightly coupled to identity DB availability
- no background tasks run in `user_service`; all work is request-driven

## Recommended Production Hardening

- move from shared header secrets to stronger service-to-service identity
- add end-to-end contract checks for `public_api -> user_service` current-user propagation
- add DB integration coverage for the API-key allocation path
