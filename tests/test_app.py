import unittest

from tradingview_service.app import create_app
from tradingview_service.cache import SimpleTTLCache
from tradingview_service.config import AppConfig
from tradingview_service.models import Bar


class FakeClient:
    def __init__(self):
        self.calls = 0

    def fetch_history(self, query):
        self.calls += 1
        return [
            Bar(time=1710000000, open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0),
            Bar(time=1710000060, open=1.5, high=2.5, low=1.0, close=2.0, volume=11.0),
        ]


class AppTests(unittest.TestCase):
    def setUp(self):
        config = AppConfig(
            tradingview_username="",
            tradingview_password="",
            cache_ttl_seconds=60,
        )
        self.fake_client = FakeClient()
        self.app = create_app(
            config,
            tv_client=self.fake_client,
            cache=SimpleTTLCache(ttl_seconds=60),
        ).test_client()

    def test_health_endpoint(self):
        response = self.app.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["port"], 6969)
        self.assertEqual(body["auth"]["mode"], "anonymous")

    def test_history_endpoint_returns_bars(self):
        response = self.app.get("/v1/history?symbol=BINANCE:BTCUSDT&interval=1m&limit=2")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["symbol"], "BINANCE:BTCUSDT")
        self.assertEqual(len(body["bars"]), 2)
        self.assertFalse(body["meta"]["cached"])
        self.assertEqual(self.fake_client.calls, 1)

    def test_history_endpoint_uses_cache(self):
        self.app.get("/v1/history?symbol=BINANCE:BTCUSDT&interval=1m&limit=2")
        response = self.app.get("/v1/history?symbol=BINANCE:BTCUSDT&interval=1m&limit=2")
        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["meta"]["cached"])
        self.assertEqual(self.fake_client.calls, 1)

    def test_history_endpoint_validates_symbol(self):
        response = self.app.get("/v1/history?symbol=BTCUSDT&interval=1m")
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()

