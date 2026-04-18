from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.identity.app.models import Base, PasswordResetToken, User
from services.identity.app.services.password_reset import (
    _hash_token,
    build_reset_url,
    consume_reset_token,
    create_reset_token,
    validate_reset_token,
)

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestSession = sessionmaker(bind=engine)


def _db():
    db = TestSession()
    return db


def _make_user(db, email="test@example.com", username="testuser"):
    user = User(email=email, username=username, password_hash="placeholder")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(db, user, *, raw="rawtoken", expired=False, used=False):
    row = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw),
        expires_at=datetime.utcnow() + (timedelta(minutes=-1) if expired else timedelta(minutes=30)),
        used=used,
    )
    db.add(row)
    db.commit()
    return raw


# --- _hash_token ---

def test_hash_token_is_deterministic():
    assert _hash_token("abc") == _hash_token("abc")


def test_hash_token_differs_for_different_inputs():
    assert _hash_token("abc") != _hash_token("xyz")


def test_hash_token_is_64_hex_chars():
    result = _hash_token("test")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


# --- build_reset_url ---

def test_build_reset_url_contains_token():
    url = build_reset_url("mytoken123")
    assert "mytoken123" in url


def test_build_reset_url_is_string():
    url = build_reset_url("token")
    assert isinstance(url, str)
    assert url.startswith("http")


# --- validate_reset_token ---

def test_validate_valid_token():
    db = _db()
    try:
        user = _make_user(db, "val@example.com", "valuser")
        raw = _make_token(db, user, raw="validtoken001")
        result = validate_reset_token(db, raw)
        assert result is not None
        assert result.id == user.id
    finally:
        db.close()


def test_validate_expired_token_returns_none():
    db = _db()
    try:
        user = _make_user(db, "exp@example.com", "expuser")
        raw = _make_token(db, user, raw="expiredtoken", expired=True)
        assert validate_reset_token(db, raw) is None
    finally:
        db.close()


def test_validate_used_token_returns_none():
    db = _db()
    try:
        user = _make_user(db, "used@example.com", "useduser")
        raw = _make_token(db, user, raw="usedtoken", used=True)
        assert validate_reset_token(db, raw) is None
    finally:
        db.close()


def test_validate_nonexistent_token_returns_none():
    db = _db()
    try:
        assert validate_reset_token(db, "doesnotexist") is None
    finally:
        db.close()


# --- create_reset_token ---

def test_create_reset_token_returns_raw_token_and_url():
    db = _db()
    try:
        user = _make_user(db, "create@example.com", "createuser")
        raw, url = create_reset_token(db, user)
        assert isinstance(raw, str)
        assert len(raw) > 10
        # IDENTITY_SHOW_RESET_LINK defaults to True and no SMTP configured
        assert url is not None
        assert raw in url
    finally:
        db.close()


def test_create_reset_token_persists_in_db():
    db = _db()
    try:
        user = _make_user(db, "persist@example.com", "persistuser")
        raw, _ = create_reset_token(db, user)
        token_hash = _hash_token(raw)
        row = db.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
        assert row is not None
        assert row.user_id == user.id
    finally:
        db.close()


# --- consume_reset_token ---

def test_consume_valid_token_returns_user():
    db = _db()
    try:
        user = _make_user(db, "consume@example.com", "consumeuser")
        raw = _make_token(db, user, raw="consumetoken1")
        result = consume_reset_token(db, raw)
        assert result is not None
        assert result.id == user.id
    finally:
        db.close()


def test_consume_token_marks_as_used():
    db = _db()
    try:
        user = _make_user(db, "mark@example.com", "markuser")
        raw = _make_token(db, user, raw="marktoken")
        consume_reset_token(db, raw)
        db.expire_all()
        row = db.query(PasswordResetToken).filter_by(token_hash=_hash_token(raw)).first()
        assert row.used is True
    finally:
        db.close()


def test_consume_token_prevents_reuse():
    db = _db()
    try:
        user = _make_user(db, "reuse@example.com", "reuseuser")
        raw = _make_token(db, user, raw="reusetoken")
        consume_reset_token(db, raw)
        second = consume_reset_token(db, raw)
        assert second is None
    finally:
        db.close()


def test_consume_nonexistent_token_returns_none():
    db = _db()
    try:
        assert consume_reset_token(db, "doesnotexist") is None
    finally:
        db.close()


def test_consume_expired_token_returns_none():
    db = _db()
    try:
        user = _make_user(db, "expcons@example.com", "expconsuser")
        raw = _make_token(db, user, raw="expiredconsume", expired=True)
        assert consume_reset_token(db, raw) is None
    finally:
        db.close()
