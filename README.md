# ProShare (Microservices Refactor)

This repository is refactored into **4 core microservices** requested in the SRS:

1. **Identity Service** (auth, profile, RBAC)
2. **Content Service** (article lifecycle, feed, search, moderation hide)
3. **Engagement Service** (likes, comments, bookmarks, reports)
4. **AI Summary Service** (summary generation, cache, regenerate rate limit, feedback)

An **API Gateway** is also provided to expose a unified API to the frontend.

## Production-oriented capabilities included
- PostgreSQL-backed persistence per service database.
- Redis-backed summary cache and regenerate throttling.
- JWT auth across services.
- Dockerized services + docker-compose orchestration.
- Service-level health endpoints.
- API gateway orchestration for summary workflow (`content -> summary`) and unified frontend access.

## Repository structure
- `services/identity` - Identity microservice.
- `services/content` - Content microservice.
- `services/engagement` - Engagement microservice.
- `services/summary` - AI summary microservice.
- `services/gateway` - Unified API gateway.
- `services/shared` - Shared security utilities.
- `frontend/` - React UI.
- `infra/init-databases.sql` - Postgres DB bootstrapping.

## Quick start (Docker)
```bash
docker compose up --build
```

Endpoints:
- Gateway: `http://localhost:8000`
- Identity: `http://localhost:8001`
- Content: `http://localhost:8002`
- Engagement: `http://localhost:8003`
- Summary: `http://localhost:8004`

## Frontend
```bash
cd frontend
npm install
npm run dev
```

By default frontend calls `http://localhost:8000`, override with `VITE_API_URL`.

## Note about old monolith
The previous `backend/` folder remains in git history for reference. The active architecture is `services/*` microservices + gateway.
