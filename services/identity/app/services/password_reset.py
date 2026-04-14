import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import settings
from ..models import PasswordResetToken, User
from .mailer import MailDeliveryError, send_password_reset_email, smtp_is_configured


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_reset_url(token: str) -> str:
    return f"{settings.PASSWORD_RESET_URL_BASE}/?reset_token={token}"


def create_reset_token(db: Session, user: User) -> tuple[str, str | None]:
    raw_token = secrets.token_urlsafe(32)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES),
    )
    db.add(token)
    db.commit()
    reset_url = build_reset_url(raw_token)

    if smtp_is_configured():
        try:
            send_password_reset_email(user.email, reset_url)
            return raw_token, None
        except MailDeliveryError:
            if settings.IDENTITY_SHOW_RESET_LINK:
                return raw_token, reset_url
            raise

    return raw_token, reset_url if settings.IDENTITY_SHOW_RESET_LINK else None


def validate_reset_token(db: Session, raw_token: str) -> User | None:
    token_hash = _hash_token(raw_token)
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not row or row.used or row.expires_at < datetime.utcnow():
        return None
    return db.query(User).filter(User.id == row.user_id).first()


def consume_reset_token(db: Session, raw_token: str) -> User | None:
    token_hash = _hash_token(raw_token)
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not row or row.used or row.expires_at < datetime.utcnow():
        return None

    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        return None

    row.used = True
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used.is_(False)).update(
        {PasswordResetToken.used: True},
        synchronize_session=False,
    )
    db.commit()
    return user
