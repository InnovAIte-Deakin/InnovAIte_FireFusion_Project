# FireFusion Backend Kubernetes Deployment

This directory contains the application deployment layer for the FireFusion Backend. It is intentionally separate from cloud infrastructure provisioning: Terraform can create an EKS, AKS or GKE cluster, while these manifests deploy the Backend workloads onto that cluster.

## Scope

The base deployment includes:

- `firefusion-api` as the public Backend entry point (`LoadBalancer` service)
- `aggregator-api` as an internal `ClusterIP` service
- `model-api` as an internal `ClusterIP` service
- Redis for forecast caching
- RabbitMQ for the existing asynchronous messaging path
- shared non-secret configuration through a ConfigMap
- DB URLs and API key supplied through a Kubernetes Secret created at deploy time
- liveness/readiness probes using `/health`
- resource requests and limits
- image-tag based deployment and Kubernetes rollout rollback

PostgreSQL is deliberately not provisioned here. The application deployment consumes database connection URLs so the target environment can use either a managed cloud database or another approved database deployment.

The AI Modelling inference API is also a separate cross-stream service. `AI_MODELLING_URL` is a placeholder in the base ConfigMap and must be overridden when the shared AI service endpoint is known.

## Prerequisites

1. A working Kubernetes cluster and configured `kubectl` context.
2. Access to the FireFusion GHCR images.
3. Reachable PostgreSQL connection URLs for FireFusion and Aggregator.
4. An Aggregator API key.

Export the required secret values:

```bash
export DB_URL='postgresql://...'
export RELATIONAL_DB_URL='postgresql://...'
export API_KEY='...'
```

If GHCR packages are private, also export:

```bash
export GHCR_USERNAME='your-github-user'
export GHCR_TOKEN='your-package-read-token'
```

Deploy the default `latest` images:

```bash
cd backend/deployment/kubernetes/scripts
./deploy.sh
./verify.sh
```

For a reproducible deployment, use a versioned image tag produced by CI:

```bash
IMAGE_TAG=sha-abcdef1 ./deploy.sh
```

Rollback the three Backend API deployments to their previous ReplicaSet revisions:

```bash
./rollback.sh
```

Clean up the application namespace with:

```bash
./cleanup.sh
```

## Cloud portability

The base manifests avoid provider-specific Kubernetes resources. The same application package is intended to sit on top of the Terraform-provisioned EKS, AKS or GKE environment. Provider-specific ingress, DNS, TLS, secret-store integration or autoscaling can be added later as overlays once the team confirms the reference cloud platform.

## CI integration

The Backend workflow renders the Kustomize package on pull requests and builds all three Backend API images. `model-api` publishing is enabled because the Kubernetes deployment requires a registry image rather than a local Docker build.

## Security notes

- No production secrets belong in Git.
- `aggregator-api`, `model-api`, Redis and RabbitMQ are internal-only services.
- Only `firefusion-api` is exposed with a cloud load balancer.
- GHCR authentication can be supplied at deploy time and is stored as a Kubernetes image-pull secret rather than in the repository.
