param(
    [string]$ClusterName = "firefusion"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required but was not found in PATH."
    }
}

function Assert-LastExitCode {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

Require-Command docker
Require-Command kubectl
Require-Command kind

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$OverlayPath = Join-Path $RepoRoot "backend\deployment\kubernetes\local"
$NamespacePath = Join-Path $RepoRoot "backend\deployment\kubernetes\base\namespace.yaml"

Push-Location $RepoRoot
try {
    $clusters = @(kind get clusters 2>$null)
    if ($clusters -notcontains $ClusterName) {
        Write-Host "Creating kind cluster '$ClusterName'..."
        kind create cluster --name $ClusterName
        Assert-LastExitCode "kind cluster creation"
    }

    kubectl config use-context "kind-$ClusterName" | Out-Null
    Assert-LastExitCode "kubectl context selection"

    Write-Host "Building FireFusion development images..."
    docker build -t firefusion-api:k8s-test backend/firefusion-api
    Assert-LastExitCode "firefusion-api image build"

    docker build -t aggregator-api:k8s-test backend/aggregator-api
    Assert-LastExitCode "aggregator-api image build"

    docker build -t model-api:k8s-test backend/model-api
    Assert-LastExitCode "model-api image build"

    Write-Host "Loading development images into kind..."
    kind load docker-image firefusion-api:k8s-test aggregator-api:k8s-test model-api:k8s-test --name $ClusterName
    Assert-LastExitCode "kind image load"

    # Ensure the namespace exists before removing a legacy standalone PostgreSQL
    # pod that may have been created during manual local testing.
    kubectl apply -f $NamespacePath | Out-Null
    Assert-LastExitCode "namespace creation"
    kubectl delete pod postgres -n firefusion --ignore-not-found=true | Out-Null

    Write-Host "Applying local Kubernetes overlay..."
    kubectl apply -k $OverlayPath
    Assert-LastExitCode "local Kubernetes deployment"

    $deployments = @(
        "redis",
        "rabbitmq",
        "postgres",
        "firefusion-api",
        "aggregator-api",
        "model-api"
    )

    foreach ($deployment in $deployments) {
        kubectl rollout status "deployment/$deployment" -n firefusion --timeout=180s
        Assert-LastExitCode "$deployment rollout"
    }

    Write-Host ""
    Write-Host "FireFusion local Kubernetes deployment is ready."
    kubectl get pods,svc -n firefusion
}
finally {
    Pop-Location
}
