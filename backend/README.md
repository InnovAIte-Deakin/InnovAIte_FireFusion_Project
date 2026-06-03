# FireFusion Backend

## How to use:

1. Ensure [Docker](https://www.docker.com/) is installed and running.
2. Run `docker compose --profile default up -d` from with in `firefusion/backend/.`

API calls should be made to `localhost:8080/api`. Information on endpoints can be found in `/firefusion-api/README.md`.

The postgres database can be accesed via `localhost:5432`.

To signal updates to the system ensure the command run:
`docker compose exec relational-db psql -U postgres "NOTIFY fire_events_channel, 'hello';"`
This will signal the system to retrieve data from the database, send to the predictive AI model and then take the model output and send to frontend clients.

## Overview

The FireFusion backend is designed as a microservice-based backend layer supporting the wider FireFusion platform. It currently contains three API services and supporting infrastructure for caching, messaging, and relational data storage.

This backend stream is responsible for:

- Exposing backend API endpoints
- Serving model inference requests
- Aggregating and processing backend data flows
- Supporting communication between services through a message broker
- Providing a containerised foundation for local development and CI/CD deployment

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

- **PostgreSQL** – Relational database for persistent storage
- **RabbitMQ** – Message broker for inter-service communication
- **Redis** – Cache for fast temporary data access

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

- Python
- FastAPI
- Uvicorn
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)
- PostgreSQL
- RabbitMQ
- Redis
- scikit-learn

---

## Local Development with Docker Compose

The backend services are intended to run together using Docker Compose.

### Current Compose Services

- `firefusion-api`
- `model-api`
- `aggregator-api`
- `relational-db`
- `broker`
- `cache`

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

- **FireFusion API:** `http://localhost:80`
- **Model API:** `http://localhost:81`
- **Aggregator API:** `http://localhost:82`
- **PostgreSQL:** `localhost:5432`
- **RabbitMQ:** `localhost:5672`
- **RabbitMQ Management UI:** `http://localhost:15672`
- **Redis:** `localhost:6379`

---

## Environment Variables

### FireFusion API

- `BROKER_URL=amqp://guest:guest@broker:5672`
- `CACHE_URL=redis://cache:6379`

### Model API

- `BROKER_URL=amqp://guest:guest@broker:5672`

### Aggregator API

- `RELATIONAL_DB_URL=postgresql://postgres:postgres@relational-db:5432/postgres`
- `BROKER_URL=amqp://guest:guest@broker:5672`

---

## Example Endpoints

### FireFusion API

- `GET /hello/`

### Model API

- `GET /`
- `GET /hello`
- `POST /predict`

### Aggregator API

- `GET /hello/`

---

## CI/CD Implementation

The backend CI/CD pipeline was implemented using **GitHub Actions**.

### CI/CD Purpose

The pipeline is designed to:

- Validate backend code changes
- Build Docker images for each backend API
- Push updated images to the container registry when changes are merged into the main branch

---

## Why This Was Needed

The FireFusion backend consists of **three separate APIs**, each with its own responsibility and Docker image.

Because of that, the CI/CD workflow must:

- Treat each API independently
- Build each service separately
- Publish separate images for deployment and orchestration

---

## Backend Images

The CI/CD workflow manages separate images for:

- `firefusion-api`
- `model-api`
- `aggregator-api`

Example registry naming pattern:

```text
ghcr.io/<owner>/<repository>/firefusion-api
ghcr.io/<owner>/<repository>/model-api
ghcr.io/<owner>/<repository>/aggregator-api
```

Images are versioned using:

- `latest`
- Commit SHA tags

---

## CI/CD Workflow Behaviour

### On Pull Requests / Pushes

The workflow performs backend validation by:

- Checking out the repository
- Setting up Python
- Installing dependencies
- Running backend test steps if available

### On Push to `main`

The workflow:

- Builds Docker images for the three backend APIs
- Authenticates with the container registry
- Pushes the latest images to the registry

---

## Container Registry

Backend images are pushed to:

```text
ghcr.io
```

---

## Why Separate Images Matter

Using separate images for the three APIs is important because:

- Each service has a different responsibility
- Each service may evolve independently
- Each service may require separate deployment or scaling
- The repository structure already reflects a microservice backend design

---

## Dockerfiles

Each backend API has its own Dockerfile:

- `backend/firefusion-api/Dockerfile`
- `backend/model-api/Dockerfile`
- `backend/aggregator-api/Dockerfile`

---

## Database Initialisation

The relational database service uses SQL initialization scripts:

- `./utilities/aggregator-init.sql`
- `./utilities/seed-aggregator.sql`

These scripts:

1. Create the required schema
2. Seed initial aggregator data

---

## Next Planned Improvements

- Define request/response models for inter-service communication
- Expand API endpoints beyond placeholder routes
- Improve health and readiness checks
- Integrate registry-based image pulls into deployment flows
- Add stronger automated testing
- Improve backend-to-backend communication patterns

---

## Summary

The FireFusion backend provides a containerised microservice foundation for the project.

It includes:

- Three backend APIs
- Supporting infrastructure via Docker Compose
- A GitHub Actions CI/CD workflow that builds and publishes separate Docker images for each API

This setup provides:

- Better modularity
- Clearer service ownership
- Improved deployment readiness
- A scalable backend foundation for the remainder of the project

---

# Beginner Guide and New Contributor Notes

## New to this backend?

If you are new to backend development, this project can feel busy at first because it runs several services together rather than one single app. That is expected for a microservice-based backend, where each service handles one part of the overall system.

A simple way to think about the FireFusion backend is:

- **FireFusion API** is the main backend entry point.
- **Model API** handles model prediction and inference tasks.
- **Aggregator API** works with the database and coordinates backend data flow.
- **PostgreSQL** stores persistent relational data.
- **RabbitMQ** passes messages between services.
- **Redis** provides fast temporary caching.

Docker Compose is used so contributors can start the full backend stack with one setup flow instead of installing and running each part manually.

---

## What to learn first

A good order for new contributors is:

1. Read this README from top to bottom.
2. Start the backend with Docker Compose.
3. Confirm the containers are healthy and ports are exposed.
4. Open the API docs in the browser.
5. Open the database and inspect the seeded tables.
6. Read the service-level `README.md` files and the main app files for each service.
7. Test one endpoint at a time before changing code.

This order helps you understand how the system fits together before you start editing implementation details.

---

## Upskilling resources

### Core setup and backend basics

- [Docker Get Started](https://www.docker.com/get-started/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Compose application model](https://docs.docker.com/compose/intro/compose-application-model/)
- [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI deployment with Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [psql documentation](https://www.postgresql.org/docs/current/app-psql.html)
- [RabbitMQ tutorials](https://www.rabbitmq.com/tutorials)
- [RabbitMQ documentation](https://www.rabbitmq.com/docs)
- [Redis documentation](https://redis.io/docs/latest/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)

### Helpful concepts to know

- **Microservices**: separate backend services with separate responsibilities.
- **API**: a defined interface for sending and receiving data.
- **Container**: an isolated runtime environment for an application.
- **Compose service**: one container definition inside the Compose configuration.
- **Message broker**: software that sends events or messages between services.
- **Inference**: using a trained model to produce a prediction.
- **Environment variables**: configuration values passed into running services.

If these ideas are new, read the linked docs while working through the setup steps below.

---

## Beginner workflow

A safe beginner workflow is:

1. Start the backend.
2. Confirm the containers are running.
3. Watch logs for the service you are testing.
4. Open the API docs in your browser.
5. Open the database and inspect the seeded data.
6. Test one endpoint and one service at a time.

Use the **VS Code terminal** for Docker and database commands. Use your **browser** for API docs and endpoint testing.

---

## Step 1: Start the backend

From the `firefusion/backend/` directory, run:

```bash
docker compose --profile default up --build -d
```

What this does:

- `docker compose` runs the multi-service stack.
- `--profile default` starts the services included in the default local development profile.
- `--build` rebuilds images if code or dependencies changed.
- `-d` runs the containers in detached mode so your terminal stays free.

If this is your first run, Docker may take a little time to build the images.

---

## Step 2: Check that services are running

After startup, run:

```bash
docker compose ps
```

This shows:

- which containers are running
- whether a service is healthy
- which local ports are mapped to each service

For this project, the main local ports are:

- **FireFusion API:** `http://localhost:8080`
- **Model API:** `http://localhost:8081`
- **Aggregator API:** `http://localhost:8082`
- **PostgreSQL:** `localhost:5432`
- **RabbitMQ:** `localhost:5672`
- **RabbitMQ Management UI:** `http://localhost:15672`
- **Redis:** `localhost:6379`

If a service is missing, stopped, or unhealthy, check its logs next.

---

## Step 3: Watch logs

To inspect live logs for the main API, run:

```bash
docker compose logs -f --tail=100 firefusion-api
```

You can replace `firefusion-api` with another service name when needed:

```bash
docker compose logs -f --tail=100 model-api
docker compose logs -f --tail=100 aggregator-api
docker compose logs -f --tail=100 relational-db
```

This is one of the most useful beginner habits. If something is not working, logs usually tell you whether the problem is startup, configuration, routing, or data related.

---

## Step 4: Open the API docs

Use your browser to open:

- `http://localhost:8080/docs`
- `http://localhost:8081/docs`
- `http://localhost:8082/docs`

These pages show the available FastAPI routes for each service. This is often the easiest way to check:

- whether the API is reachable
- what endpoints exist
- what request and response formats are expected

If `/docs` loads but `/` returns `404`, that usually just means the app does not define a root homepage route.

---

## Step 5: Open the database

To open the PostgreSQL shell, run this in the VS Code terminal:

```bash
docker compose exec relational-db psql -U postgres
```

Once inside `psql`, useful starter commands are:

```sql
\dn
\dt *.*
```

What these do:

- `\dn` lists schemas
- `\dt *.*` lists tables across schemas

For FireFusion, focus on the tables in the `public` schema, such as:

- `fire_events`
- `weather_conditions`
- `topography`
- `fuel_and_vegetation`
- `at_risk_infrastructure`

To inspect seeded data, run queries such as:

```sql
SELECT * FROM fire_events;
SELECT * FROM weather_conditions;
SELECT * FROM topography;
SELECT * FROM fuel_and_vegetation;
SELECT * FROM at_risk_infrastructure;
```

If the output is too long, use `LIMIT`:

```sql
SELECT * FROM fire_events LIMIT 10;
```

The many `pg_toast` rows you may see in `\dt *.*` are PostgreSQL internal tables. They are normal and can usually be ignored.

---

## Step 6: Test the backend flow

The main backend API base path is:

```text
http://localhost:8080/api
```

Endpoint details can be found in:

```text
/firefusion-api/README.md
```

You can also test endpoints directly in the browser or from the FastAPI docs page.

If an endpoint returns `null`, that usually means the route exists and ran successfully, but the backend returned no actual data yet. In practice, this often means the route returned `None` or the service method did not produce a populated response.

---

## Step 7: Trigger backend update processing

To signal updates to the system, run:

```bash
docker compose exec relational-db psql -U postgres -c "NOTIFY fire_events_channel, 'hello';"
```

What this does:

- connects to the PostgreSQL container
- sends a `NOTIFY` event on the `fire_events_channel`
- allows listening parts of the system to react to new or updated database state

In this project, that signal is intended to trigger a backend processing flow where data is retrieved from the database, passed into the predictive model, and then sent onward to connected frontend clients.

If this command fails, first confirm that:

- the `relational-db` container is running
- `psql` opens correctly
- the backend services are up and healthy

---

## Step 8: Read the service folders

Once the stack is running and you have confirmed the APIs and database work, inspect each service folder:

- `backend/firefusion-api`
- `backend/model-api`
- `backend/aggregator-api`

Start with these files:

- `README.md`
- `Dockerfile`
- `requirements.txt`
- main application files inside `app/`

This will help you connect the running containers to the actual code and responsibilities.

---

## Common troubleshooting

### Docker runs but no services appear

Check:

```bash
docker compose ps
```

If no services are selected or nothing starts, make sure you are:

- in the correct folder
- using the correct Compose file
- running with the `default` profile

Recommended command:

```bash
docker compose --profile default up --build -d
```

### A service starts but the browser shows an error

Check:

- that you are using the correct port
- that the container is running in `docker compose ps`
- that the service logs show startup completed

Then open the relevant `/docs` page to confirm the API is live.

### The API docs load but an endpoint returns `null`

This usually means:

- the route exists
- the request reached the backend
- the route returned no populated response

Check:

- whether the database tables contain data
- whether the endpoint's service code actually reads that data
- whether the service method returns a real object, string, or dictionary rather than `None`

### The database looks empty

If the expected seeded tables or rows do not appear, the initialisation scripts may not have run on the current volume. To reset the database and rerun the init scripts:

```bash
docker compose down -v
docker compose --profile default up --build -d
```

Be careful: `-v` removes volumes and clears stored database data.

### Logs do not show much

That can be normal if the service is idle. Keep the log command running and then trigger a request in the browser. For example:

```bash
docker compose logs -f --tail=100 firefusion-api
```

Then refresh:

```text
http://localhost:8080/docs
```

or call an endpoint. New requests should appear in the logs.

### psql shows strange syntax errors after pasting

If you see odd characters such as `[200~`, your terminal likely pasted control characters into `psql`. Press `Ctrl + C` to clear the current line, then type the SQL command manually instead of pasting it.

---

## Good habits for new contributors

- Read the root README before editing code.
- Check `docker compose ps` before assuming something is broken.
- Use service-specific logs when debugging.
- Confirm ports before testing endpoints.
- Query the database directly when API data looks wrong.
- Test one service and one change at a time.
- Rebuild after changing dependencies, Dockerfiles, or environment configuration.
- Use `docker compose down -v` only when you intentionally want a fresh database state.

---

## Recommended first success checklist

A good first milestone for a new contributor is:

1. Run `docker compose --profile default up --build -d`
2. Run `docker compose ps`
3. Open `http://localhost:8080/docs`
4. Run `docker compose exec relational-db psql -U postgres`
5. Run `\dt *.*`
6. Run `SELECT * FROM fire_events LIMIT 10;`
7. Open the service folders and identify where `/api/bushfire-forecast` is implemented

If you can complete those steps, your local backend environment is set up correctly and you are ready to start reading and changing code.

---

## Support note

If you are new to Docker, FastAPI, PostgreSQL, or message-driven backend systems, work through this guide in order rather than jumping straight into the code. The fastest way to debug this project is usually:

1. check container status
2. check logs
3. check API docs
4. check database state
5. then inspect the service code
