#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-firefusion}"

command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required" >&2; exit 1; }

kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
