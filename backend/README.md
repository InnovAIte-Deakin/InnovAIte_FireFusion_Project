# FireFusion Backend

## Overview

The FireFusion backend is designed as a microservice-based backend layer supporting the wider FireFusion platform. It currently contains three API services and supporting infrastructure for caching, messaging, and relational data storage.

This backend stream is responsible for:

* Exposing backend API endpoints
* Serving model inference requests
* Aggregating and processing backend data flows
* Supporting communication between services through a message broker
* Providing a containerised foundation for local development and CI/CD deployment

---

## Backend Services

### FireFusion API

Main API service for the platform and primary backend entry point for core application interactions.

**Path:** `backend/firefusion-api`

---

### Model API

Model-serving API for prediction and inference tasks.

**Path:** `backend/model-api`

---

### Aggregator API

API service responsible for aggregation-oriented backend logic and interactions with the relational database and broker.

**Path:** `backend/aggregator-api`

---

## Supporting Services

The backend stack also relies on:

* **PostgreSQL** – Relational database for persistent storage
* **RabbitMQ** – Message broker for inter-service communication
* **Redis** – Cache for fast temporary data access

---

## Repository Structure

```text
backend/
├── firefusion-api/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── model-api/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── model.pkl
│   └── README.md
├── aggregator-api/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
└── README.md
```

---

## Technologies Used

* Python
* FastAPI
* Uvicorn
* Docker
* Docker Compose
* GitHub Actions
* GitHub Container Registry (GHCR)
* PostgreSQL
* RabbitMQ
* Redis
* scikit-learn

---

## Local Development with Docker Compose

The backend services are intended to run together using Docker Compose.

### Current Compose Services

* `firefusion-api`
* `model-api`
* `aggregator-api`
* `relational-db`
* `broker`
* `cache`

---

## Running the Backend Locally

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

Stop and remove volumes:

```bash
docker compose down -v
```

---

## Current Local Ports

* **FireFusion API:** `http://localhost:80`
* **Model API:** `http://localhost:81`
* **Aggregator API:** `http://localhost:82`
* **PostgreSQL:** `localhost:5432`
* **RabbitMQ:** `localhost:5672`
* **RabbitMQ Management UI:** `http://localhost:15672`
* **Redis:** `localhost:6379`

---

## Environment Variables

### FireFusion API

* `BROKER_URL=amqp://guest:guest@broker:5672`
* `CACHE_URL=redis://cache:6379`

### Model API

* `BROKER_URL=amqp://guest:guest@broker:5672`

### Aggregator API

* `RELATIONAL_DB_URL=postgresql://postgres:postgres@relational-db:5432/postgres`
* `BROKER_URL=amqp://guest:guest@broker:5672`

---

## Example Endpoints

### FireFusion API

* `GET /hello/`

### Model API

* `GET /`
* `GET /hello`
* `POST /predict`

### Aggregator API

* `GET /hello/`

---

## CI/CD Implementation

The backend CI/CD pipeline was implemented using **GitHub Actions**.

### CI/CD Purpose

The pipeline is designed to:

* Validate backend code changes
* Build Docker images for each backend API
* Push updated images to the container registry when changes are merged into the main branch

---

## Why This Was Needed

The FireFusion backend consists of **three separate APIs**, each with its own responsibility and Docker image.

Because of that, the CI/CD workflow must:

* Treat each API independently
* Build each service separately
* Publish separate images for deployment and orchestration

---

## Backend Images

The CI/CD workflow manages separate images for:

* `firefusion-api`
* `model-api`
* `aggregator-api`

Example registry naming pattern:

```text
ghcr.io/<owner>/<repository>/firefusion-api
ghcr.io/<owner>/<repository>/model-api
ghcr.io/<owner>/<repository>/aggregator-api
```

Images are versioned using:

* `latest`
* Commit SHA tags

---

## CI/CD Workflow Behaviour

### On Pull Requests / Pushes

The workflow performs backend validation by:

* Checking out the repository
* Setting up Python
* Installing dependencies
* Running backend test steps if available

### On Push to `main`

The workflow:

* Builds Docker images for the three backend APIs
* Authenticates with the container registry
* Pushes the latest images to the registry

---

## Container Registry

Backend images are pushed to:

```text
ghcr.io
```

---

## Why Separate Images Matter

Using separate images for the three APIs is important because:

* Each service has a different responsibility
* Each service may evolve independently
* Each service may require separate deployment or scaling
* The repository structure already reflects a microservice backend design

---

## Dockerfiles

Each backend API has its own Dockerfile:

* `backend/firefusion-api/Dockerfile`
* `backend/model-api/Dockerfile`
* `backend/aggregator-api/Dockerfile`

---

## Database Initialisation

The relational database service uses SQL initialization scripts:

* `./utilities/aggregator-init.sql`
* `./utilities/seed-aggregator.sql`

These scripts:

1. Create the required schema
2. Seed initial aggregator data

---

## Next Planned Improvements

* Define request/response models for inter-service communication
* Expand API endpoints beyond placeholder routes
* Improve health and readiness checks
* Integrate registry-based image pulls into deployment flows
* Add stronger automated testing
* Improve backend-to-backend communication patterns

---

## Summary

The FireFusion backend provides a containerised microservice foundation for the project.

It includes:

* Three backend APIs
* Supporting infrastructure via Docker Compose
* A GitHub Actions CI/CD workflow that builds and publishes separate Docker images for each API

This setup provides:

* Better modularity
* Clearer service ownership
* Improved deployment readiness
* A scalable backend foundation for the remainder of the project
