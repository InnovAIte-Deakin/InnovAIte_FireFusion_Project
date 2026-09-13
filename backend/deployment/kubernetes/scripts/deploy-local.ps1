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
$BootstrapOverlayPath = Join-Path $RepoRoot "backend\deployment\kubernetes\local-bootstrap"
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

    kubectl apply -f $NamespacePath | Out-Null
    Assert-LastExitCode "namespace creation"

    # Local development state is disposable. Recreate deployments so repeated
    # runs avoid immutable-selector drift from earlier manifest revisions and
    # always start from the images that were just built and loaded.
    kubectl delete deployment firefusion-api aggregator-api model-api redis rabbitmq postgres -n firefusion --ignore-not-found=true | Out-Null
    Assert-LastExitCode "existing local deployment cleanup"
    kubectl delete pod postgres -n firefusion --ignore-not-found=true | Out-Null

    # Apply the complete local configuration with API replicas temporarily set
    # to zero. This creates services, config, secrets and dependencies without
    # allowing FastAPI startup to race RabbitMQ/PostgreSQL readiness.
    Write-Host "Bootstrapping local infrastructure dependencies..."
    kubectl apply -k $BootstrapOverlayPath
    Assert-LastExitCode "local bootstrap deployment"

    $dependencies = @("redis", "rabbitmq", "postgres")
    foreach ($dependency in $dependencies) {
        kubectl rollout status "deployment/$dependency" -n firefusion --timeout=180s
        Assert-LastExitCode "$dependency rollout"
    }

    Write-Host "Dependencies are ready. Starting Backend APIs..."
    kubectl apply -k $OverlayPath
    Assert-LastExitCode "local Kubernetes deployment"

    $apis = @("firefusion-api", "aggregator-api", "model-api")
    foreach ($api in $apis) {
        kubectl rollout status "deployment/$api" -n firefusion --timeout=180s
        Assert-LastExitCode "$api rollout"
    }

    Write-Host ""
    Write-Host "FireFusion local Kubernetes deployment is ready."
    kubectl get pods,svc -n firefusion
}
finally {
    Pop-Location
}
