import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from services.shared.app.database import build_engine
from services.shared.app.security import decode_token

from .models import Base, User

DATABASE_URL = os.getenv("IDENTITY_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_identity")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
auth = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(credentials.credentials, JWT_SECRET)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user
