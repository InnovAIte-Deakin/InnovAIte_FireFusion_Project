# Backend tests

A first testing baseline for the FireFusion backend. Two layers:

- **Unit** (`test_data_geojson.py`): no running stack needed, runs anywhere.
- **Integration** (`test_smoke_*.py`, marked `integration`): hit the three
  services over HTTP. They skip automatically if a service is not reachable,
  so `pytest` is safe to run with the stack down.

## Run locally

Start the stack first (from `backend/`):

```bash
docker compose --profile default up --build -d
```

Then:

```bash
pip install -r tests/requirements-test.txt
pytest tests
```

Run only the fast unit tests (no Docker needed):

```bash
pytest tests -m "not integration"
```

Service URLs default to localhost:8080/8081/8082 and can be overridden with
`FF_URL`, `MODEL_URL`, `AGG_URL` environment variables.

## What is covered

- firefusion-api: service up, `/hello/`, `/api/bushfire-forecast` returns JSON,
  the misinformation list endpoints return lists, unknown id returns 404.
- model-api: `/model/hello`, `/model/geojson` returns GeoJSON.
- aggregator-api: service up, `/hello/` is rejected without a valid API key.

## CI

`.github/workflows/backend-tests.yml` boots the stack with Docker Compose,
waits for the services, and runs this suite on every push to `main` and every
pull request that touches `backend/`.

## Next

- Add tests for the RabbitMQ pipeline (DB NOTIFY to prediction to WebSocket push).
- Add per-service unit tests that mock the broker and database so more logic is
  covered without the full stack.
