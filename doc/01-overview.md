# Overview

## Service Purpose

`user_service` is the internal account and user administration service for
Manifeed. It provides backend-only endpoints for:

- authenticated account reads
- account profile updates
- password changes
- user API key lifecycle
- admin user listing and admin-managed flag updates

This service is designed for trusted internal consumers, not public/browser
clients.

## Responsibilities

- Read account state from the identity database
- Update mutable account fields (`pseudo`, `pp_id`)
- Change passwords and revoke active sessions afterward
- Create and revoke user API keys
- Build worker-facing API key projections (`worker_name`, visible prefix)
- List users with admin filters and pagination
- Update admin-managed user flags
- Revalidate account requests through `auth_service`
- Enforce internal service token authorization
- Expose health/readiness probes for orchestrators
- Emit shared request logs and shared JSON error payloads

## Technical Stack

- FastAPI
- SQLAlchemy + psycopg + PostgreSQL
- `manifeed-shared-backend` for shared schemas/domain/errors
- `auth_service` for session resolution on account flows
