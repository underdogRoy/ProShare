# ProShare Recommended Microservice Split (MVP -> v1.0)

This plan balances fast MVP delivery with a clean path to independent scaling.

## Suggested services

### 1) API Gateway / BFF
- Public entry point used by web frontend.
- Handles authentication, rate limiting, and request shaping.
- Routes to internal services over REST.

### 2) Identity Service
- Owns user accounts, login/logout, profile, RBAC.
- Tables: users, sessions, profile metadata.
- FR mapping: FR-01, FR-02, NFR-01, NFR-02.

### 3) Content Service
- Owns article lifecycle (draft/edit/publish/update), tags, feeds.
- Exposes recent/trending/search APIs.
- Tables: articles, article_tags, content_reports.
- FR mapping: FR-03..FR-08, FR-16.

### 4) Engagement Service
- Owns likes/claps, comments, bookmarks, summary feedback.
- Tables: reactions, comments, bookmarks, summary_feedback.
- FR mapping: FR-09..FR-11, FR-15.

### 5) Summary Service
- Owns AI summarization pipeline, caching, regeneration limits.
- Uses job queue for long-form chunking + merge.
- Tables/Cache: summary_cache, regenerate_log, job_status.
- FR mapping: FR-12..FR-14, NFR-03, NFR-05, NFR-07.

### 6) Moderation Service (can start in monolith)
- Owns report triage, admin hide/remove workflow, audit logs.
- FR mapping: FR-16, FR-17.

## Rollout strategy
1. **Phase 1 (now)**: Keep a modular monolith (`backend`) + separate `ai` service.
2. **Phase 2**: Extract Identity and Summary first (clear boundaries, independent scale).
3. **Phase 3**: Extract Engagement and Moderation.
4. **Phase 4**: Introduce API Gateway and optional event bus.

## Data and communication guidelines
- Each service owns its database schema (no cross-service table writes).
- Prefer synchronous REST for reads and command-style writes.
- Introduce async events for feed score recompute and moderation workflows.
- Use idempotency keys for summary generation and feedback writes.

## Why this split is practical
- Summary workloads are bursty and expensive; isolating them protects core article UX.
- Engagement traffic has high write volume and benefits from separate tuning.
- Identity changes are security-sensitive and should be isolated early.
