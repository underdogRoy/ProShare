# Frontend hierarchy

- `app/`
  - Auth pages: `login`, `register`
  - Discovery pages: `recent`, `trending`, `search`, `tags/[tag]`
  - Article pages: `articles/[id]`, `editor`
  - Admin page: `admin`
- `components/`
  - `ArticleCard`, `SummaryPanel`, `CommentSection`, `Editor`
- `hooks/`
  - `useArticles`, `useSummary`
- `lib/`
  - Shared API client
