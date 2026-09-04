# Reviewer Notes

This contribution adds the Backend application deployment layer on top of the project's cloud infrastructure work.

It deliberately does not add or replace Terraform for EKS, AKS, or GKE. The Kubernetes package is cloud-neutral and can be applied after a target managed Kubernetes cluster is provisioned.

Key review areas:

- Kubernetes Deployments/Services for FireFusion API, Aggregator API, Model API, Redis, and RabbitMQ
- runtime ConfigMap/Secret wiring
- readiness/liveness probes and resource requests/limits
- local `kind` overlay and dependency-first bootstrap for reproducible testing
- health endpoints and smoke tests
- GitHub Actions manifest rendering and image build/push support
- deployment, verification, rollback, and cleanup scripts

Known integration dependency: `AI_MODELLING_URL` currently points to the expected internal service URL and will need alignment with the AI Modelling stream's final Kubernetes service name/port.
