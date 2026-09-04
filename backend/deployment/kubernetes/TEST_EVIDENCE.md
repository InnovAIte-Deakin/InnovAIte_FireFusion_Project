# Local Kubernetes Validation Evidence

Validated on Windows with Docker Desktop, `kind`, and `kubectl` using the `firefusion` kind cluster.

## Deployment result

The dependency-first local deployment completed successfully with all six runtime deployments available:

- `firefusion-api` - `1/1`, `Running`, `0` restarts
- `aggregator-api` - `1/1`, `Running`, `0` restarts
- `model-api` - `1/1`, `Running`, `0` restarts
- PostgreSQL - `1/1`, `Running`, `0` restarts
- RabbitMQ - `1/1`, `Running`, `0` restarts
- Redis - `1/1`, `Running`, `0` restarts

## Internal service smoke test

`verify-local.ps1` created a temporary in-cluster curl pod and successfully resolved and called all three Kubernetes Services:

```text
{"status":"healthy","service":"firefusion-api"}
{"status":"healthy","service":"aggregator-api"}
{"status":"healthy","service":"model-api"}
```

This validates Kubernetes Service DNS/network routing and the `/health` endpoints for the three Backend APIs.

## Issues found and fixed during validation

- RabbitMQ probe timeouts were too short and caused unnecessary restarts. Probe timeout was increased to 5 seconds.
- API deployments initially started before RabbitMQ was ready and failed with `AMQPConnectionError: Connection refused`. The local bootstrap now starts dependencies first, waits for readiness, and then starts the Backend APIs.
- Deprecated Kustomize `commonLabels` was replaced with `labels` without mutating existing Deployment selectors.
- The Aggregator image no longer bakes a default API key into the Docker image; local Docker Compose and Kubernetes supply it at runtime.

## Scope note

The local overlay contains disposable PostgreSQL and test-only credentials for development validation. The production/base Kubernetes package does not deploy PostgreSQL and expects database credentials and URLs to be supplied through Kubernetes Secrets or the target cloud platform's approved secret/configuration mechanism.
