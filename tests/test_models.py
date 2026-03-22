import unittest

from tradingview_service.errors import ValidationError
from tradingview_service.models import Bar, HistoryQuery, build_history_payload, filter_bars


class ModelTests(unittest.TestCase):
    def test_history_query_rejects_deep_window(self):
        with self.assertRaises(ValidationError):
            HistoryQuery.from_args(
                {
                    "symbol": "BINANCE:BTCUSDT",
                    "interval": "1m",
                    "from": "1700000000",
                    "to": "1700003600",
                },
                default_limit=500,
                max_limit=5000,
                now_ts=1710000000,
            )

    def test_filter_bars_applies_bounds_and_limit(self):
        query = HistoryQuery.from_args(
            {
                "symbol": "BINANCE:BTCUSDT",
                "interval": "1m",
                "from": "1710000000",
                "to": "1710000120",
                "limit": "2",
            },
            default_limit=500,
            max_limit=5000,
            now_ts=1710000200,
        )
        bars = [
            Bar(time=1709999940, open=1, high=1, low=1, close=1, volume=1),
            Bar(time=1710000000, open=1, high=1, low=1, close=1, volume=1),
            Bar(time=1710000060, open=2, high=2, low=2, close=2, volume=2),
            Bar(time=1710000120, open=3, high=3, low=3, close=3, volume=3),
        ]
        filtered = filter_bars(bars, query)
        self.assertEqual([bar.time for bar in filtered], [1710000060, 1710000120])

    def test_build_payload_sets_meta_fields(self):
        query = HistoryQuery.from_args(
            {"symbol": "BINANCE:BTCUSDT", "interval": "1m", "limit": "1"},
            default_limit=500,
            max_limit=5000,
        )
        payload = build_history_payload(
            query,
            [Bar(time=1710000000, open=1, high=2, low=0.5, close=1.5, volume=10)],
            cached=False,
        )
        self.assertEqual(payload["meta"]["count"], 1)
        self.assertEqual(payload["meta"]["from"], 1710000000)


if __name__ == "__main__":
    unittest.main()
