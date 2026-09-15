param(
    [string]$Namespace = "firefusion"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required but was not found in PATH."
    }
}

Require-Command kubectl

$deployments = @("firefusion-api", "aggregator-api", "model-api")
foreach ($deployment in $deployments) {
    kubectl wait --for=condition=Available "deployment/$deployment" -n $Namespace --timeout=120s
    if ($LASTEXITCODE -ne 0) {
        throw "$deployment is not available."
    }
}

kubectl delete pod firefusion-smoke-test -n $Namespace --ignore-not-found=true | Out-Null

kubectl run firefusion-smoke-test `
    -n $Namespace `
    --restart=Never `
    --image=curlimages/curl:8.10.1 `
    -- sh -ec "curl -fsS http://firefusion-api/health && echo && curl -fsS http://aggregator-api:8080/health && echo && curl -fsS http://model-api:8080/health && echo"

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create smoke-test pod."
}

$phase = ""
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    $phase = kubectl get pod firefusion-smoke-test -n $Namespace -o jsonpath='{.status.phase}'
    if ($phase -eq "Succeeded") {
        break
    }
    if ($phase -eq "Failed") {
        kubectl logs firefusion-smoke-test -n $Namespace
        throw "Internal Kubernetes smoke test failed."
    }
    Start-Sleep -Seconds 2
}

if ($phase -ne "Succeeded") {
    kubectl describe pod firefusion-smoke-test -n $Namespace
    throw "Smoke test timed out before reaching Succeeded state."
}

Write-Host "Internal service health responses:"
kubectl logs firefusion-smoke-test -n $Namespace
if ($LASTEXITCODE -ne 0) {
    throw "Could not read smoke-test logs."
}

kubectl delete pod firefusion-smoke-test -n $Namespace --ignore-not-found=true | Out-Null

Write-Host ""
Write-Host "Internal Kubernetes service health checks passed."
kubectl get pods,svc -n $Namespace
