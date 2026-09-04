#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-firefusion}"

command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required" >&2; exit 1; }

for deployment in firefusion-api aggregator-api model-api; do
  echo "Rolling back $deployment..."
  kubectl rollout undo "deployment/$deployment" -n "$NAMESPACE"
  kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=180s
done

kubectl get deployments -n "$NAMESPACE"
echo "Backend API deployments rolled back to their previous ReplicaSet revisions."
