import unittest

from tradingview_service.market_data import MarketDataService
from tradingview_service.models import Bar


class FakeClient:
    def __init__(self):
        self.calls = []

    def fetch_history(self, query):
        self.calls.append(query)
        return [
            Bar(time=1710000000, open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0),
            Bar(time=1710000060, open=1.5, high=2.5, low=1.0, close=2.0, volume=11.0),
        ]


class FakeCache:
    def __init__(self):
        self.store = {}
        self.get_calls = []
        self.set_calls = []

    def get(self, key):
        self.get_calls.append(key)
        return self.store.get(key)

    def set(self, key, value):
        self.set_calls.append((key, value))
        self.store[key] = value


class MarketDataServiceTests(unittest.TestCase):
    def setUp(self):
        self.fake_client = FakeClient()
        self.fake_cache = FakeCache()
        self.service = MarketDataService(
            self.fake_client,
            self.fake_cache,
            default_limit=500,
            max_limit=5000,
        )

    def test_get_history_returns_route_payload_shape(self):
        payload = self.service.get_history(
            {"symbol": "BINANCE:BTCUSDT", "interval": "1m", "limit": "2"}
        )

        self.assertEqual(payload["symbol"], "BINANCE:BTCUSDT")
        self.assertEqual(payload["interval"], "1m")
        self.assertEqual(payload["timezone"], "UTC")
        self.assertEqual(
            payload["bars"],
            [
                {
                    "time": 1710000000,
                    "open": 1.0,
                    "high": 2.0,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 10.0,
                },
                {
                    "time": 1710000060,
                    "open": 1.5,
                    "high": 2.5,
                    "low": 1.0,
                    "close": 2.0,
                    "volume": 11.0,
                },
            ],
        )
        self.assertEqual(
            payload["meta"],
            {
                "count": 2,
                "from": 1710000000,
                "to": 1710000060,
                "cached": False,
            },
        )

    def test_get_history_uses_cache(self):
        args = {"symbol": "BINANCE:BTCUSDT", "interval": "1m", "limit": "2"}

        first_payload = self.service.get_history(args)
        second_payload = self.service.get_history(args)

        self.assertFalse(first_payload["meta"]["cached"])
        self.assertTrue(second_payload["meta"]["cached"])
        self.assertEqual(len(self.fake_client.calls), 1)

    def test_cached_payload_does_not_mutate_stored_meta(self):
        args = {"symbol": "BINANCE:BTCUSDT", "interval": "1m", "limit": "2"}

        self.service.get_history(args)
        stored_payload = next(iter(self.fake_cache.store.values()))
        cached_payload = self.service.get_history(args)

        self.assertFalse(stored_payload["meta"]["cached"])
        self.assertTrue(cached_payload["meta"]["cached"])
        self.assertEqual(len(self.fake_client.calls), 1)


if __name__ == "__main__":
    unittest.main()
