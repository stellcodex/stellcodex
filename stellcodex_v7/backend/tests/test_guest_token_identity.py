import unittest

from app.security.jwt import create_guest_token, decode_token


class GuestTokenIdentityTests(unittest.TestCase):
    def test_guest_token_contains_stable_sub_and_owner_sub(self) -> None:
        token = create_guest_token(owner_sub="guest-123", anon=True)
        payload = decode_token(token)

        self.assertEqual(payload["typ"], "guest")
        self.assertEqual(payload["sub"], "guest:guest-123")
        self.assertEqual(payload["owner_sub"], "guest-123")
        self.assertTrue(payload["anon"])

    def test_guest_token_normalizes_prefixed_owner_sub(self) -> None:
        token = create_guest_token(owner_sub="guest:abc-42", anon=True)
        payload = decode_token(token)

        self.assertEqual(payload["sub"], "guest:abc-42")
        self.assertEqual(payload["owner_sub"], "abc-42")


if __name__ == "__main__":
    unittest.main()
