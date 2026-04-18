import pytest

from services.shared.app.security import create_token, decode_token, decode_token_payload, hash_password, verify_password


def test_password_hashing():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)


def test_jwt_round_trip():
    token = create_token(42, "unit-test-secret", minutes=5)
    assert decode_token(token, "unit-test-secret") == 42


def test_wrong_password_fails():
    hashed = hash_password("correct-password")
    assert not verify_password("wrong-password", hashed)


def test_different_hashes_for_same_password():
    h1 = hash_password("mypassword")
    h2 = hash_password("mypassword")
    assert h1 != h2  # bcrypt/pbkdf2 uses random salt


def test_invalid_jwt_raises():
    with pytest.raises(ValueError):
        decode_token("not.a.valid.token", "any-secret")


def test_wrong_secret_raises():
    token = create_token(99, "secret-a", minutes=5)
    with pytest.raises(ValueError):
        decode_token(token, "secret-b")


def test_expired_jwt_raises():
    token = create_token(7, "test-secret", minutes=-1)
    with pytest.raises(ValueError):
        decode_token(token, "test-secret")


def test_admin_flag_in_token():
    token = create_token(10, "test-secret", is_admin=True)
    payload = decode_token_payload(token, "test-secret")
    assert payload["is_admin"] is True
    assert payload["sub"] == 10


def test_non_admin_flag_defaults_false():
    token = create_token(11, "test-secret", is_admin=False)
    payload = decode_token_payload(token, "test-secret")
    assert payload["is_admin"] is False
