# ProShare

A professional article-sharing platform built on a microservices architecture. Users can write, publish, and explore articles, engage with the community through likes, bookmarks and comments, and generate AI-powered summaries using the Claude API.

## Architecture

Four core backend microservices sit behind a unified API gateway:

| Service | Responsibility |
|---|---|
| **Identity** | Registration, login, JWT auth, password reset, user profiles, RBAC |
| **Content** | Article creation, editing, deletion, feed, search, admin moderation |
| **Engagement** | Likes, bookmarks, comments, reports |
| **Summary** | AI summary generation via Claude API, Redis caching, regenerate throttling, feedback |
| **Notifications** | In-app notifications for likes, bookmarks, and comments on your articles |

An **API Gateway** exposes a single endpoint to the frontend and orchestrates cross-service workflows (e.g. fetching article content before calling the summary service).

## Repository structure

```
services/
  identity/       Identity microservice
  content/        Content microservice
  engagement/     Engagement microservice
  summary/        AI summary microservice (Claude-powered)
  notifications/  Notifications microservice
  gateway/        Unified API gateway
  shared/         Shared JWT security utilities
frontend/         React + Vite single-page app
infra/            Postgres DB bootstrap SQL
scripts/          Local dev scripts (Windows/PowerShell)
```

## Quick start (Docker)

**1. Copy and fill in your environment file:**
```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**2. Start the full stack:**
```bash
docker compose up --build
```

Service ports:
- Frontend (dev): `http://localhost:5173`
- Gateway: `http://localhost:8000`
- Identity: `http://localhost:8001`
- Content: `http://localhost:8002`
- Engagement: `http://localhost:8003`
- Summary: `http://localhost:8004`
- Notifications: `http://localhost:8005`

**3. Run the frontend dev server separately:**
```bash
cd frontend
npm install
npm run dev
```

By default the frontend calls `http://localhost:8000`. Override with `VITE_API_URL` if needed.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for AI summaries) | Claude API key for article summarisation |
| `JWT_SECRET` | Recommended | Secret used to sign JWT tokens. Defaults to `dev-secret` |
| `PASSWORD_RESET_URL_BASE` | No | Frontend base URL used in password reset links |
| `SMTP_PROVIDER` | No | `gmail` or `outlook` shortcut |
| `SMTP_HOST`, `SMTP_PORT` | No | Override SMTP server directly |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | No | SMTP login credentials |
| `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` | No | Sender identity shown to users |
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | No | Transport security flags |
| `IDENTITY_SHOW_RESET_LINK` | No | When `true`, returns a dev reset link if SMTP is not configured |

## AI Summary (Claude)

The summary service calls `claude-haiku-4-5-20251001` to generate a TL;DR and key takeaways for any article. Features:
- HTML and base64 image content is stripped before sending to the model
- Long articles are split into chunks, each summarised, then combined
- Results are cached in Redis for one hour (keyed by article content hash)
- A regenerate option bypasses the cache with a 30-second rate limit per user
- Falls back to a basic extractive summary if no API key is configured

## Frontend features

- **Explore** — community article feed with search and sort (by time, likes, comments, bookmarks); sidebar showing your recently liked and bookmarked articles
- **Write** — rich text editor (Quill) with image upload; images are embedded at the cursor position
- **My Articles** — manage your drafts and published posts; edit or delete your own articles
- **Article view** — two-column layout: article body on the left, AI summary panel on the right; engagement stats, report form, and comments below
- **Profile** — bio, expertise tags, portfolio links, and a writing portfolio view
- **Admin** — report review and article moderation (hide, unhide, delete) for admin users
- **Notifications** — bell icon in the header with an unread badge; shows when someone likes, bookmarks, or comments on your articles; polls every 30 seconds and supports mark-as-read

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

## Quick start (Windows, no Docker)

Requirements: Python 3.10+, Node.js 18+, PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-local.ps1
.\scripts\start-local.ps1
```

In local mode, services use SQLite under `.local-data/` and the summary cache is in-memory.

```powershell
.\scripts\start-local.ps1 -NoFrontend   # backend only
.\scripts\stop-local.ps1                # stop everything
```
