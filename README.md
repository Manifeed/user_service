# Manifeed User Service

Standalone FastAPI service extracted from the former backend monolith.

It consumes `shared_backend` for shared schemas, shared auth contracts, and
internal service token validation helpers.

## Run Locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Build from the monorepo root:

```bash
docker build -t manifeed-user-service -f user_service/Dockerfile .
```

The runtime image is multi-stage, runs as a non-root user, and installs
`shared_backend` from a wheel built locally from the monorepo.
