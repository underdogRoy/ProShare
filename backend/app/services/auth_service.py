"""Auth domain logic."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_token, hash_password, verify_password
from app.models.models import User
from app.schemas.auth import RegisterRequest, TokenPair


def register_user(payload: RegisterRequest, db: Session) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise ValueError("EMAIL_EXISTS")
    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(email: str, password: str, db: Session) -> TokenPair:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("INVALID_CREDENTIALS")
    return TokenPair(
        access_token=create_token(
            str(user.id), settings.access_token_expire_minutes, "access"
        ),
        refresh_token=create_token(
            str(user.id), settings.refresh_token_expire_minutes, "refresh"
        ),
    )
