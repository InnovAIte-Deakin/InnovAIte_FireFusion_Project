#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-firefusion}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../base" && pwd)"
IMAGE_ROOT="ghcr.io/innovaite-deakin/innovaite_firefusion_project"

required=(kubectl DB_URL RELATIONAL_DB_URL API_KEY)
for item in "${required[@]}"; do
  if [[ "$item" == "kubectl" ]]; then
    command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required" >&2; exit 1; }
  elif [[ -z "${!item:-}" ]]; then
    echo "$item must be exported before deployment" >&2
    exit 1
  fi
done

kubectl apply -f "$BASE_DIR/namespace.yaml"

kubectl create secret generic firefusion-backend-secrets \
  --namespace "$NAMESPACE" \
  --from-literal=DB_URL="$DB_URL" \
  --from-literal=RELATIONAL_DB_URL="$RELATIONAL_DB_URL" \
  --from-literal=API_KEY="$API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  kubectl create secret docker-registry ghcr-pull-secret \
    --namespace "$NAMESPACE" \
    --docker-server=ghcr.io \
    --docker-username="$GHCR_USERNAME" \
    --docker-password="$GHCR_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -

  kubectl patch serviceaccount default -n "$NAMESPACE" \
    --type=merge \
    -p '{"imagePullSecrets":[{"name":"ghcr-pull-secret"}]}'
fi

kubectl apply -k "$BASE_DIR"

kubectl set image deployment/firefusion-api \
  firefusion-api="$IMAGE_ROOT/firefusion-api:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/aggregator-api \
  aggregator-api="$IMAGE_ROOT/aggregator-api:$IMAGE_TAG" -n "$NAMESPACE"
kubectl set image deployment/model-api \
  model-api="$IMAGE_ROOT/model-api:$IMAGE_TAG" -n "$NAMESPACE"

for deployment in redis rabbitmq firefusion-api aggregator-api model-api; do
  echo "Waiting for $deployment..."
  kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=180s
done

kubectl get pods,svc -n "$NAMESPACE"

echo "Deployment applied with image tag: $IMAGE_TAG"
echo "Run ./verify.sh to test service health from inside the cluster."
