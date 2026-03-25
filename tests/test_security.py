from services.shared.app.security import create_token, decode_token, hash_password, verify_password


def test_password_hashing():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)


def test_jwt_round_trip():
    token = create_token(42, "unit-test-secret", minutes=5)
    assert decode_token(token, "unit-test-secret") == 42
