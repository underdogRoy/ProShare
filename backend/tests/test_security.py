from app.core.security import create_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("supersecret")
    assert verify_password("supersecret", hashed)


def test_token_creation() -> None:
    token = create_token("1", 5, "access")
    assert isinstance(token, str)
    assert len(token) > 20
