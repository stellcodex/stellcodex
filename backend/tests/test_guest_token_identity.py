from app.security.jwt import create_guest_token, decode_token


def test_guest_token_contains_stable_sub_and_owner_sub() -> None:
    token = create_guest_token(owner_sub="guest-123", anon=True)
    payload = decode_token(token)

    assert payload["typ"] == "guest"
    assert payload["sub"] == "guest:guest-123"
    assert payload["owner_sub"] == "guest-123"
    assert payload["anon"] is True


def test_guest_token_normalizes_prefixed_owner_sub() -> None:
    token = create_guest_token(owner_sub="guest:abc-42", anon=True)
    payload = decode_token(token)

    assert payload["sub"] == "guest:abc-42"
    assert payload["owner_sub"] == "abc-42"
