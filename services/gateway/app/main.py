import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

def _with_scheme(url: str) -> str:
    """Add https:// to bare hostnames injected by Render's fromService.host."""
    if url and not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


IDENTITY = _with_scheme(os.getenv("IDENTITY_URL", "http://localhost:8001"))
CONTENT = _with_scheme(os.getenv("CONTENT_URL", "http://localhost:8002"))
ENGAGEMENT = _with_scheme(os.getenv("ENGAGEMENT_URL", "http://localhost:8003"))
SUMMARY = _with_scheme(os.getenv("SUMMARY_URL", "http://localhost:8004"))
NOTIFICATIONS = _with_scheme(os.getenv("NOTIFICATIONS_URL", "http://localhost:8005"))
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origin.strip()
]

app = FastAPI(title="ProShare API Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://[a-z0-9-]+\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def request_json(method: str, url: str, request: Request | None = None, json_body: dict | None = None):
    headers = {}
    params = None
    body = None
    if request is not None:
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length", "accept-encoding"}}
        params = request.query_params
        if json_body is None:
            body = await request.body()

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.request(method, url, headers=headers, params=params, content=body, json=json_body)

    if resp.status_code >= 400:
        detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"detail": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json() if resp.text else {"ok": True}


async def attach_author_usernames(articles: list[dict]) -> list[dict]:
    if not articles:
        return articles

    author_ids = sorted({article.get("author_id") for article in articles if article.get("author_id") is not None})
    if not author_ids:
        return articles

    try:
        users = await request_json("GET", f"{IDENTITY}/users/batch?ids={','.join(str(user_id) for user_id in author_ids)}")
    except HTTPException:
        return articles

    usernames = {user["id"]: user["username"] for user in users if user.get("id") is not None and user.get("username")}
    for article in articles:
        article["author_username"] = usernames.get(article.get("author_id"))
    return articles


async def _get_article_author(article_id: int, auth_header: str) -> int | None:
    headers = {"authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{CONTENT}/articles/{article_id}", headers=headers)
    if resp.status_code == 200:
        return resp.json().get("author_id")
    return None


async def _fire_notification(article_id: int, recipient_user_id: int, notif_type: str, auth_header: str):
    headers = {"authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(
            f"{NOTIFICATIONS}/notifications",
            json={"recipient_user_id": recipient_user_id, "article_id": article_id, "type": notif_type},
            headers=headers,
        )


async def _enrich_notifications(notifications: list[dict], auth_header: str) -> list[dict]:
    if not notifications:
        return notifications

    actor_ids = sorted({n["actor_user_id"] for n in notifications if n.get("actor_user_id") is not None})
    article_ids = sorted({n["article_id"] for n in notifications if n.get("article_id") is not None})

    usernames: dict = {}
    titles: dict = {}

    if actor_ids:
        try:
            users = await request_json("GET", f"{IDENTITY}/users/batch?ids={','.join(str(i) for i in actor_ids)}")
            usernames = {u["id"]: u["username"] for u in users if u.get("id") is not None}
        except HTTPException:
            pass

    if article_ids:
        try:
            headers = {"authorization": auth_header} if auth_header else {}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{CONTENT}/articles/batch",
                    params={"ids": ",".join(str(i) for i in article_ids)},
                    headers=headers,
                )
            if resp.status_code == 200:
                titles = {a["id"]: a["title"] for a in resp.json() if a.get("id") is not None and a.get("title")}
        except Exception:
            pass

    for n in notifications:
        n["actor_username"] = usernames.get(n.get("actor_user_id"))
        n["article_title"] = titles.get(n.get("article_id"))

    return notifications


async def attach_comment_usernames(comments: list[dict]) -> list[dict]:
    if not comments:
        return comments

    user_ids = sorted({comment.get("user_id") for comment in comments if comment.get("user_id") is not None})
    if not user_ids:
        return comments

    try:
        users = await request_json("GET", f"{IDENTITY}/users/batch?ids={','.join(str(user_id) for user_id in user_ids)}")
    except HTTPException:
        return comments

    usernames = {user["id"]: user["username"] for user in users if user.get("id") is not None and user.get("username")}
    for comment in comments:
        comment["username"] = usernames.get(comment.get("user_id"))
    return comments


@app.get('/health')
def health():
    return {"ok": True}


@app.api_route('/auth/{path:path}', methods=['GET', 'POST', 'PUT'])
async def auth_proxy(path: str, request: Request):
    return await request_json(request.method, f"{IDENTITY}/auth/{path}", request=request)


@app.api_route('/users/{path:path}', methods=['GET', 'POST', 'PUT'])
async def users_proxy(path: str, request: Request):
    return await request_json(request.method, f"{IDENTITY}/users/{path}", request=request)


async def _fetch_user_articles(engagement_path: str, auth_header: str) -> list:
    headers = {"authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=20) as client:
        eng_resp = await client.get(engagement_path, headers=headers)
    if eng_resp.status_code >= 400:
        detail = eng_resp.json() if eng_resp.headers.get("content-type", "").startswith("application/json") else {"detail": eng_resp.text}
        raise HTTPException(status_code=eng_resp.status_code, detail=detail)
    article_ids = eng_resp.json() if eng_resp.text else []
    if not article_ids:
        return []
    ids_str = ",".join(str(i) for i in article_ids)
    async with httpx.AsyncClient(timeout=20) as client:
        content_resp = await client.get(
            f"{CONTENT}/articles/batch",
            params={"ids": ids_str},
            headers=headers,
        )
    if content_resp.status_code >= 400:
        detail = content_resp.json() if content_resp.headers.get("content-type", "").startswith("application/json") else {"detail": content_resp.text}
        raise HTTPException(status_code=content_resp.status_code, detail=detail)
    articles = content_resp.json() if content_resp.text else []
    return await attach_author_usernames(articles)


@app.api_route('/me/likes', methods=['GET'])
async def my_liked_articles(request: Request):
    limit = request.query_params.get("limit", "0")
    auth = request.headers.get("authorization", "")
    return await _fetch_user_articles(f"{ENGAGEMENT}/me/likes?limit={limit}", auth)


@app.api_route('/me/bookmarks', methods=['GET'])
async def my_bookmarked_articles(request: Request):
    limit = request.query_params.get("limit", "0")
    auth = request.headers.get("authorization", "")
    return await _fetch_user_articles(f"{ENGAGEMENT}/me/bookmarks?limit={limit}", auth)


@app.api_route('/articles', methods=['POST'])
async def create_article(request: Request):
    return await request_json(request.method, f"{CONTENT}/articles", request=request)


@app.api_route('/articles/mine', methods=['GET'])
async def my_articles(request: Request):
    articles = await request_json(request.method, f"{CONTENT}/articles/mine", request=request)
    return await attach_author_usernames(articles)


@app.api_route('/articles/{article_id}', methods=['GET'])
async def get_article(article_id: int, request: Request):
    article = await request_json('GET', f"{CONTENT}/articles/{article_id}", request=request)
    enriched = await attach_author_usernames([article])
    return enriched[0] if enriched else article


@app.api_route('/articles/{article_id}/summary', methods=['POST'])
async def summary_generate(article_id: int, request: Request):
    regenerate = request.query_params.get("regenerate", "false").lower() == "true"
    article = await request_json("GET", f"{CONTENT}/articles/{article_id}", request=request)
    payload = {"article_id": article_id, "content": article["content"], "regenerate": regenerate}
    headers = {"authorization": request.headers.get("authorization", "")}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{SUMMARY}/summary/generate", json=payload, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@app.api_route('/articles/{article_id}/summary/feedback', methods=['POST'])
async def summary_feedback(article_id: int, request: Request):
    body = await request.json()
    payload = {"article_id": article_id, **body}
    headers = {"authorization": request.headers.get("authorization", "")}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{SUMMARY}/summary/feedback", json=payload, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    return resp.json()


@app.api_route('/articles/{article_id}/{action}', methods=['POST'])
async def engagement_actions(article_id: int, action: str, request: Request):
    result = await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/{action}", request=request)
    should_notify = (action in ('like', 'bookmark') and result.get('created')) or action == 'comments'
    if should_notify:
        try:
            auth_header = request.headers.get('authorization', '')
            author_id = await _get_article_author(article_id, auth_header)
            if author_id:
                notif_type = 'comment' if action == 'comments' else action
                await _fire_notification(article_id, author_id, notif_type, auth_header)
        except Exception:
            pass
    return result


@app.api_route('/articles/{article_id}/comments', methods=['GET', 'POST'])
async def article_comments(article_id: int, request: Request):
    payload = await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/comments", request=request)
    if request.method == "GET" and isinstance(payload, list):
        return await attach_comment_usernames(payload)
    return payload


@app.api_route('/articles/{article_id}/stats', methods=['GET'])
async def article_stats(article_id: int, request: Request):
    return await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/stats", request=request)


@app.api_route('/articles/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def articles_proxy(path: str, request: Request):
    return await request_json(request.method, f"{CONTENT}/articles/{path}", request=request)


async def _enrich_and_sort(articles: list, sort: str) -> list:
    if not articles:
        return articles
    await attach_author_usernames(articles)
    ids = ",".join(str(a["id"]) for a in articles)
    try:
        stats_map = await request_json('GET', f"{ENGAGEMENT}/articles/batch-stats?ids={ids}")
    except Exception:
        stats_map = {}
    for article in articles:
        s = stats_map.get(str(article["id"]), {})
        article["like_count"] = s.get("like_count", 0)
        article["comment_count"] = s.get("comment_count", 0)
        article["bookmark_count"] = s.get("bookmark_count", 0)
    if sort == "likes":
        articles.sort(key=lambda a: a["like_count"], reverse=True)
    elif sort == "comments":
        articles.sort(key=lambda a: a["comment_count"], reverse=True)
    elif sort == "bookmarks":
        articles.sort(key=lambda a: a["bookmark_count"], reverse=True)
    return articles


@app.api_route('/feeds/recent', methods=['GET'])
async def feeds_recent(request: Request):
    sort = request.query_params.get("sort", "time")
    articles = await request_json('GET', f"{CONTENT}/feeds/recent", request=request)
    return await _enrich_and_sort(articles, sort)


@app.api_route('/feeds/{path:path}', methods=['GET'])
async def feeds_proxy(path: str, request: Request):
    return await request_json('GET', f"{CONTENT}/feeds/{path}", request=request)


@app.api_route('/search', methods=['GET'])
async def search_proxy(request: Request):
    sort = request.query_params.get("sort", "time")
    articles = await request_json('GET', f"{CONTENT}/search", request=request)
    return await _enrich_and_sort(articles, sort)


@app.api_route('/notifications/unread-count', methods=['GET'])
async def notifications_unread_count(request: Request):
    return await request_json('GET', f"{NOTIFICATIONS}/notifications/unread-count", request=request)


@app.api_route('/notifications/read-all', methods=['PATCH'])
async def notifications_read_all(request: Request):
    return await request_json('PATCH', f"{NOTIFICATIONS}/notifications/read-all", request=request)


@app.api_route('/notifications/{notification_id}/read', methods=['PATCH'])
async def notification_mark_read(notification_id: int, request: Request):
    return await request_json('PATCH', f"{NOTIFICATIONS}/notifications/{notification_id}/read", request=request)


@app.api_route('/notifications', methods=['GET'])
async def list_notifications(request: Request):
    notifications = await request_json('GET', f"{NOTIFICATIONS}/notifications", request=request)
    if not isinstance(notifications, list):
        return notifications
    auth_header = request.headers.get('authorization', '')
    return await _enrich_notifications(notifications, auth_header)


@app.api_route('/reports', methods=['POST'])
async def report_proxy(request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/reports", request=request)


@app.api_route('/admin/reports', methods=['GET'])
async def admin_reports(request: Request):
    reports = await request_json('GET', f"{ENGAGEMENT}/admin/reports", request=request)
    enriched = []
    for report in reports:
        article = None
        if report.get("target_type") == "article":
            try:
                article = await request_json("GET", f"{CONTENT}/admin/articles/{report['target_id']}", request=request)
            except HTTPException:
                article = None
        enriched.append({**report, "article": article})
    return enriched


@app.api_route('/admin/articles', methods=['GET'])
async def admin_articles(request: Request):
    payload = await request_json('GET', f"{CONTENT}/admin/articles", request=request)
    items = payload.get("items", [])
    payload["items"] = await attach_author_usernames(items)
    return payload


@app.api_route('/admin/articles/{article_id}/{action}', methods=['POST'])
async def admin_article_action(article_id: int, action: str, request: Request):
    return await request_json('POST', f"{CONTENT}/admin/articles/{article_id}/{action}", request=request)


@app.api_route('/admin/reports/resolve', methods=['POST'])
async def admin_resolve_report(request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/admin/reports/resolve", request=request)


@app.api_route('/admin/reports/{report_id}/reopen', methods=['POST'])
async def admin_reopen_report(report_id: int, request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/admin/reports/{report_id}/reopen", request=request)
