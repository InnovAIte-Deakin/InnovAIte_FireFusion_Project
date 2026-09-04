# Local smoke-test result

The local `kind` workflow was validated successfully on Windows with Docker Desktop and `kubectl`.

All runtime components reached `Running` with zero restarts after dependency-first bootstrap:

- `firefusion-api` - 1/1
- `aggregator-api` - 1/1
- `model-api` - 1/1
- PostgreSQL - 1/1
- RabbitMQ - 1/1
- Redis - 1/1

The in-cluster smoke test then returned:

```text
{"status":"healthy","service":"firefusion-api"}
{"status":"healthy","service":"aggregator-api"}
{"status":"healthy","service":"model-api"}
```

This confirms the three Backend API health endpoints and Kubernetes Service-to-Service DNS/networking in the local test environment.
