# Manifeed User Service

Standalone FastAPI service extracted from the former backend monolith.

## Run Locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
