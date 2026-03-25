import os

import httpx
from fastapi import FastAPI, HTTPException, Request

IDENTITY = os.getenv("IDENTITY_URL", "http://localhost:8001")
CONTENT = os.getenv("CONTENT_URL", "http://localhost:8002")
ENGAGEMENT = os.getenv("ENGAGEMENT_URL", "http://localhost:8003")
SUMMARY = os.getenv("SUMMARY_URL", "http://localhost:8004")

app = FastAPI(title="ProShare API Gateway")


async def request_json(method: str, url: str, request: Request | None = None, json_body: dict | None = None):
    headers = {}
    params = None
    body = None
    if request is not None:
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        params = request.query_params
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


@app.api_route('/articles/{path:path}', methods=['GET', 'POST', 'PUT'])
async def articles_proxy(path: str, request: Request):
    return await request_json(request.method, f"{CONTENT}/articles/{path}", request=request)


@app.api_route('/feeds/{path:path}', methods=['GET'])
async def feeds_proxy(path: str, request: Request):
    return await request_json('GET', f"{CONTENT}/feeds/{path}", request=request)


@app.api_route('/search', methods=['GET'])
async def search_proxy(request: Request):
    return await request_json('GET', f"{CONTENT}/search", request=request)


@app.api_route('/reports', methods=['POST'])
async def report_proxy(request: Request):
    return await request_json('POST', f"{ENGAGEMENT}/reports", request=request)
