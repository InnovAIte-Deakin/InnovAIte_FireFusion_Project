#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-firefusion}"

command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required" >&2; exit 1; }

kubectl wait --for=condition=Available deployment/firefusion-api -n "$NAMESPACE" --timeout=120s
kubectl wait --for=condition=Available deployment/aggregator-api -n "$NAMESPACE" --timeout=120s
kubectl wait --for=condition=Available deployment/model-api -n "$NAMESPACE" --timeout=120s

kubectl run firefusion-smoke-test \
  --namespace "$NAMESPACE" \
  --rm -i --restart=Never \
  --image=curlimages/curl:8.10.1 \
  -- sh -ec '
    curl -fsS http://firefusion-api/health
    echo
    curl -fsS http://aggregator-api:8080/health
    echo
    curl -fsS http://model-api:8080/health
    echo
  '

echo "Internal Kubernetes service health checks passed."
kubectl get service firefusion-api -n "$NAMESPACE"
