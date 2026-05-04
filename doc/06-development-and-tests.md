# Development and Testing

## Local Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Minimum local environment:

```bash
export APP_ENV=local
export IDENTITY_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_identity
export AUTH_SERVICE_URL=http://localhost:8001
```

Run service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Build from monorepo root:

```bash
docker build -t manifeed-user-service -f user_service/Dockerfile .
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

## Tests

Run all tests:

```bash
pytest -q
```

Current test coverage:

- source syntax validation
- wrapped `payload` route contract
- invalid session handling on account routes
- admin role enforcement on admin routes
- account service password update side effects
- nested transaction retry behavior for API key allocation
- networking payload contracts for upstream callers

Recommended next tests:

- DB integration tests for profile/password/API-key flows
- end-to-end container tests for `public_api -> user_service -> auth_service`
- admin-service integration tests with real user fixtures

## Runtime Base

The container build now targets `python:3.13-slim`.
