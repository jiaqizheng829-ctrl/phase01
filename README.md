# Greenhouse Dashboard — Phase 1

This project is the Phase 1 foundation for a Greenhouse Dashboard application.

## Included in Phase 1

- PostgreSQL database running with Docker Compose
- FastAPI backend
- Database health-check endpoint
- Alembic baseline migration
- Scalar API documentation
- React + TypeScript + Vite frontend
- Tailwind CSS dashboard placeholder
- Frontend health-status display

## Project structure

```text
phase01/
├── backend/
│   ├── alembic/
│   ├── app/
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
└── questions.md
