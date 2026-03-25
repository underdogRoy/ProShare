# ProShare Microservice Architecture (Implemented)

## Implemented services

### 1) Identity Service (`services/identity`)
- Register / login / profile update.
- Password hashing + JWT issuing.
- RBAC field (`is_admin`) included in user model.

### 2) Content Service (`services/content`)
- Create/edit/publish articles.
- Read article detail with draft privacy checks.
- Recent feed and keyword search.
- Admin hide endpoint for moderation execution.

### 3) Engagement Service (`services/engagement`)
- Like, bookmark, comments.
- Report content.
- Stats endpoint for article engagement counts.

### 4) AI Summary Service (`services/summary`)
- Generate summary (TL;DR + bullets).
- Regenerate summary with per-user rate limiting.
- Redis cache for fast reuse.
- Summary feedback collection.

### API Gateway (`services/gateway`)
- Single entry point for frontend.
- Routes requests to each microservice.
- Orchestrates summary use case by fetching article content from content service and passing it to summary service.

## Data and infra
- PostgreSQL: separate DB per service (identity/content/engagement/summary).
- Redis: summary cache + throttle keys.
- Docker Compose: full local stack boot.
