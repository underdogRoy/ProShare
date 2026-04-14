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

## Quick start (Windows, no Docker)
This repository now includes a local development mode for Windows:

- Service databases run on local `SQLite` files under `.local-data/`
- Summary cache falls back to in-memory storage, so local dev does not require Redis
- You can start the whole stack with PowerShell scripts

Requirements:
- Python 3.10+
- Node.js 18+
- PowerShell

From the repo root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-local.ps1
.\scripts\start-local.ps1
```

Endpoints in local mode:
- Gateway: `http://127.0.0.1:8000`
- Identity: `http://127.0.0.1:8001`
- Content: `http://127.0.0.1:8002`
- Engagement: `http://127.0.0.1:8003`
- Summary: `http://127.0.0.1:8004`
- Frontend: `http://127.0.0.1:5173`

Helpful commands:

```powershell
# Start backend services only
.\scripts\start-local.ps1 -NoFrontend

# Stop everything started by the local script
.\scripts\stop-local.ps1
```

Notes:
- Local SQLite files are created automatically in `.local-data/`
- Summary cache is in-memory during local mode, so restarting the summary service clears cached summaries
- The Docker workflow still uses PostgreSQL + Redis as before

## Password Reset Email Setup
The identity service supports real SMTP delivery for password reset emails.

Recommended setup:
1. Copy `.env.example` to `.env`
2. Fill in your Gmail address and Google App Password
3. Start the stack with `docker compose up --build`
4. Keep the frontend running at `http://localhost:5173` so reset links open correctly

Example Gmail template:
```env
PASSWORD_RESET_URL_BASE=http://localhost:5173
SMTP_PROVIDER=gmail
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_16_digit_google_app_password
SMTP_FROM_EMAIL=your_gmail@gmail.com
SMTP_FROM_NAME=ProShare
SMTP_USE_TLS=true
SMTP_USE_SSL=false
IDENTITY_SHOW_RESET_LINK=false
```

Environment variables:
- `PASSWORD_RESET_URL_BASE` - frontend base URL used in reset links
- `SMTP_PROVIDER` - optional shortcut such as `gmail` or `outlook`
- `SMTP_HOST`, `SMTP_PORT` - override SMTP server details directly
- `SMTP_USERNAME`, `SMTP_PASSWORD` - SMTP login credentials
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` - sender identity shown to users
- `SMTP_USE_TLS`, `SMTP_USE_SSL` - transport security flags
- `IDENTITY_SHOW_RESET_LINK` - when `true`, the API also returns a development reset link if SMTP is not configured

Common presets:
- Gmail: set `SMTP_PROVIDER=gmail` and use an app password for `SMTP_PASSWORD`
- Outlook/Hotmail: set `SMTP_PROVIDER=outlook`

For Gmail:
1. Open your Google Account security settings
2. Turn on `2-Step Verification`
3. Create an `App Password`
4. Paste that generated 16-character password into `SMTP_PASSWORD`

If SMTP is not configured, password reset still works in development mode by returning a preview reset link from the identity service.

## Admin Testing Notes
- Register a normal user account first.
- In the identity database, update that user's `is_admin` field to `true`.
- Sign out and sign back in so a fresh token includes admin access.
- The frontend will then show an `Admin` tab for report review and article moderation.

## Frontend
```bash
cd frontend
npm install
npm run dev
```

By default frontend calls `http://localhost:8000`, override with `VITE_API_URL`.

## Note about old monolith
The previous `backend/` folder remains in git history for reference. The active architecture is `services/*` microservices + gateway.
