import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

IDENTITY = os.getenv("IDENTITY_URL", "http://localhost:8001")
CONTENT = os.getenv("CONTENT_URL", "http://localhost:8002")
ENGAGEMENT = os.getenv("ENGAGEMENT_URL", "http://localhost:8003")
SUMMARY = os.getenv("SUMMARY_URL", "http://localhost:8004")
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origin.strip()
]

app = FastAPI(title="ProShare API Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def request_json(method: str, url: str, request: Request | None = None, json_body: dict | None = None):
    headers = {}
    params = None
    body = None
    if request is not None:
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
        params = request.query_params
        if json_body is None:
            body = await request.body()

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.request(method, url, headers=headers, params=params, content=body, json=json_body)

    if resp.status_code >= 400:
        detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"detail": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json() if resp.text else {"ok": True}


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
    return content_resp.json() if content_resp.text else []


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
    return await request_json(request.method, f"{CONTENT}/articles/mine", request=request)


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
    return await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/{action}", request=request)


@app.api_route('/articles/{article_id}/comments', methods=['GET', 'POST'])
async def article_comments(article_id: int, request: Request):
    return await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/comments", request=request)


@app.api_route('/articles/{article_id}/stats', methods=['GET'])
async def article_stats(article_id: int, request: Request):
    return await request_json(request.method, f"{ENGAGEMENT}/articles/{article_id}/stats", request=request)


@app.api_route('/articles/{path:path}', methods=['GET', 'POST', 'PUT'])
async def articles_proxy(path: str, request: Request):
    return await request_json(request.method, f"{CONTENT}/articles/{path}", request=request)


async def _enrich_and_sort(articles: list, sort: str) -> list:
    if not articles:
        return articles
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


@app.api_route('/admin/articles/{article_id}/{action}', methods=['POST'])
async def admin_article_action(article_id: int, action: str, request: Request):
    return await request_json('POST', f"{CONTENT}/admin/articles/{article_id}/{action}", request=request)


@app.api_route('/admin/reports/resolve', methods=['POST'])
async def admin_resolve_report(request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/admin/reports/resolve", request=request)


@app.api_route('/admin/reports/{report_id}/reopen', methods=['POST'])
async def admin_reopen_report(report_id: int, request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/admin/reports/{report_id}/reopen", request=request)
