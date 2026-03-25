# Backend API Contracts

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/refresh`

## Users
- `GET /users/{id}`
- `PUT /users/{id}`
- `GET /users/{id}/articles`

## Articles & Discovery
- `POST /articles`
- `GET /articles`
- `GET /articles/{id}`
- `PUT /articles/{id}`
- `DELETE /articles/{id}`
- `POST /articles/{id}/publish`
- `GET /articles/search?q=...`
- `GET /articles/tags/{tag}`
- `GET /articles/trending`
- `GET /articles/recent`

## Engagement
- `POST /articles/{id}/like`
- `DELETE /articles/{id}/like`
- `POST /articles/{id}/comments`
- `GET /articles/{id}/comments`
- `POST /articles/{id}/bookmark`
- `DELETE /articles/{id}/bookmark`

## Summary
- `POST /articles/{id}/summary`
- `GET /articles/{id}/summary`
- `POST /articles/{id}/summary/feedback`

## Moderation
- `POST /reports`
- `GET /reports` (admin)
- `PATCH /reports/{id}/status` (admin)
- `DELETE /articles/{id}` (admin)
- `DELETE /comments/{id}` (admin)
