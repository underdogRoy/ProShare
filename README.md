# ProShare v1.0 Monorepo

Production-oriented modular scaffold for a professional knowledge-sharing
platform with AI summaries.

## Modules
- `frontend/`: Next.js app (UI, hooks, pages, tests)
- `backend/`: FastAPI REST API, SQLAlchemy models, migration SQL, tests
- `ai/`: AI summarization FastAPI + Celery worker, chunking/cache pipeline
- `infra/`: Docker Compose, CI workflow, architecture docs

## Quick start
1. Copy `.env.example` to `.env` and edit secrets.
2. Start services: `docker compose -f infra/docker-compose.yml up -d --build`
3. Backend API: `http://localhost:8000/docs`
4. Frontend: `http://localhost:3000`
5. AI service: `http://localhost:8100/docs`

## Schema
Initial SQL migration is in `backend/alembic/versions/20260325_01_init.sql`.

## Testing
- Frontend: `cd frontend && npm test`
- Backend: `cd backend && pytest`
- AI: `cd ai && pytest`
