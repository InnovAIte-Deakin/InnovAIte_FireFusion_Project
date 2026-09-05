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

PostgreSQL is deliberately not provisioned in the cloud base. The application deployment consumes database connection URLs so the target environment can use either a managed cloud database or another approved database deployment.

The AI Modelling inference API is also a separate cross-stream service. `AI_MODELLING_URL` is a placeholder in the base ConfigMap and must be overridden when the shared AI service endpoint is known.

## Local Kubernetes validation on Windows

The `local/` overlay is for a disposable developer `kind` cluster only. It adds a local PostgreSQL instance, test-only credentials, the three locally built `k8s-test` API images and `imagePullPolicy: Never` so Kubernetes uses images loaded directly into the kind node.

Prerequisites:

- Docker Desktop
- `kubectl`
- `kind`
- Windows PowerShell

From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File backend/deployment/kubernetes/scripts/deploy-local.ps1
```

This script creates or reuses the `firefusion` kind cluster, builds the three API images, loads them into the node, applies the local Kustomize overlay and waits for all deployments to complete.

Run the internal Kubernetes DNS/service smoke test with:

```powershell
powershell -ExecutionPolicy Bypass -File backend/deployment/kubernetes/scripts/verify-local.ps1
```

For browser testing of the public Backend entry point on a development machine where port 8080 is already in use, forward another local port, for example:

```powershell
kubectl port-forward svc/firefusion-api -n firefusion 18080:80
```

Then open `http://localhost:18080/health`.

The credentials and PostgreSQL deployment under `local/` are intentionally development-only and must not be used in a shared or production environment.

## Shared/cloud deployment prerequisites

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
- The credentials under `local/` are fixed test values for disposable local clusters only.
