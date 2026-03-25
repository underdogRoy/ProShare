from fastapi import FastAPI

from ai.app.api.routes import router

app = FastAPI(title="ProShare AI", version="1.0.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
