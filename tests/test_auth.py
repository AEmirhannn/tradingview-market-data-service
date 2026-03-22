import io
import json
import unittest

from tradingview_service.auth import TradingViewAuthenticator
from tradingview_service.errors import AuthenticationError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class AuthTests(unittest.TestCase):
    def test_returns_unauthorized_token_without_credentials(self):
        auth = TradingViewAuthenticator("", "", timeout_seconds=5)
        self.assertEqual(auth.get_token(), "unauthorized_user_token")

    def test_fetches_and_caches_auth_token(self):
        calls = []

        def opener(request, timeout):
            calls.append((request.full_url, timeout))
            return FakeResponse({"user": {"auth_token": "abc123"}})

        auth = TradingViewAuthenticator("user", "pass", timeout_seconds=5, opener=opener)
        self.assertEqual(auth.get_token(), "abc123")
        self.assertEqual(auth.get_token(), "abc123")
        self.assertEqual(len(calls), 1)

    def test_raises_when_auth_token_missing(self):
        def opener(request, timeout):
            return FakeResponse({"error": "bad credentials"})

        auth = TradingViewAuthenticator("user", "pass", timeout_seconds=5, opener=opener)
        with self.assertRaises(AuthenticationError):
            auth.get_token(force_refresh=True)


if __name__ == "__main__":
    unittest.main()

