#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-firefusion}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../base" && pwd)"

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

kubectl apply -k "$BASE_DIR"

for deployment in redis rabbitmq firefusion-api aggregator-api model-api; do
  echo "Waiting for $deployment..."
  kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=180s
done

kubectl get pods,svc -n "$NAMESPACE"

echo "Deployment applied. Run ./verify.sh to test service health from inside the cluster."
