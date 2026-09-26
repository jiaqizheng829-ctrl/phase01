# Phase 3 — Abstract Factory

- [Phase 3 questions and answers](phases/phase-03/questions.md)
- [Abstract Factory implementation notes](docs/patterns/abstract-factory.md)

Phase 3 answers use the provided questions.md template and its original Your Answer fields.

---




# Greenhouse Dashboard — Phase 1

A basic three-tier application using React, FastAPI, and PostgreSQL.
Phase 1 sets up the project foundation without business tables or design patterns.

## Requirements

- Docker Desktop installed and its engine running
- Ports 5173, 8000, and 5432 available

## Start the application

Download or clone this repository. Open a terminal in the project root,
the folder containing docker-compose.yml.

Build and start the three services:

```bash
docker compose up -d --build
```

Check their status:

```bash
docker compose ps
```

Wait for PostgreSQL to be ready. Then apply the baseline migration:

```bash
docker compose exec backend alembic upgrade head
```

Check the database migration version:

```bash
docker compose exec backend alembic current
```

The expected revision is `001_baseline`.

## Open the application

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Health check: http://localhost:8000/health
- Scalar API documentation: http://localhost:8000/scalar
- OpenAPI JSON: http://localhost:8000/openapi.json

The default `/docs` and `/redoc` pages are disabled.

## Verify the application

When the backend can connect to PostgreSQL, `/health` should return:

```json
{
  "status": "ok",
  "db": "ok"
}
```

The frontend should display:

```text
Backend and database are healthy
```

Check that the Scalar page loads and lists the health endpoint.

## Environment configuration

Docker Compose supplies the database connection settings to the backend.
A separate .env file is not required for the current Docker setup.

The root .env.example contains example settings for running the backend
directly on the host computer. It is not automatically loaded from the
project root when the backend is started from another directory.

The sample credentials are for local coursework only.

## Frontend checks

Build the frontend:

```bash
docker compose exec frontend npm run build
```

Run TypeScript checking separately:

```bash
docker compose exec frontend npx tsc --noEmit
```

## Troubleshooting

If a service fails, inspect its logs:

```bash
docker compose logs backend db frontend
```

If Docker reports that it cannot connect to the engine, check Docker Desktop
before running the project commands again.

## Stop the application

```bash
docker compose down
```

This stops the services and keeps the database volume.

## Phase 1 answers

The answers to the Phase 1 skeleton questions are in questions.md.

## Verification status

End-to-end runtime verification is pending.
The commands and expected results above still need to be checked on a running system.

## Reference

I compared my Phase 1 implementation with the course example and used it
to guide corrections to the backend layers, health endpoint, and API
documentation. Parts of these corrections were adapted from the example.

Course example:
https://github.com/xamk-mire/DesignPatterns-Example-Project/tree/main/Example-project
