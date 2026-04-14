from fastapi import FastAPI

from .deps import Base, engine
from .routes import auth, users

app = FastAPI(title="Identity Service")
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth.router)
app.include_router(users.router)
