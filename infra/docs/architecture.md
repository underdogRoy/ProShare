# ProShare v1.0 Architecture

```mermaid
flowchart LR
  FE[Next.js Frontend] -->|REST| BE[FastAPI Backend]
  BE -->|SQLAlchemy| PG[(PostgreSQL)]
  BE -->|enqueue| R[(Redis)]
  AIW[Celery Worker] -->|consume| R
  BE -->|HTTP generate| AIS[AI FastAPI Service]
  AIS -->|cache| R
  AIW --> PG
```

## Integration contracts
- `POST /articles/{id}/summary` triggers AI summary generation/fetch.
- Redis keys follow `article:{id}:summary:{method}`.
- AI service returns `summary` plus disclaimer.

## Deployment notes
- Render/Fly/AWS/GCP deployments can reuse container images from module Dockerfiles.
- Use managed PostgreSQL + Redis in production.
