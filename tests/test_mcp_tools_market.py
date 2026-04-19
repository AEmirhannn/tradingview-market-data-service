import unittest
from types import SimpleNamespace

from tradingview_service.errors import ValidationError
from tradingview_service.mcp.tools_market import MarketDataMCPTools


class FakeAuthenticator:
    def health(self):
        return {
            "mode": "anonymous",
            "state": "anonymous",
            "last_refresh_at": None,
            "last_error": None,
        }


class FakeService:
    default_limit = 500
    max_limit = 5000

    def __init__(self, payloads=None):
        self.calls = []
        self.payloads = list(payloads or [])

    def get_history(self, args):
        args = dict(args)
        self.calls.append(args)
        if self.payloads:
            return self.payloads.pop(0)
        return {
            "symbol": args["symbol"],
            "interval": args["interval"],
            "timezone": "UTC",
            "bars": [
                {
                    "time": 1710000000,
                    "open": 100.0,
                    "high": 105.0,
                    "low": 99.0,
                    "close": 104.0,
                    "volume": 10.0,
                },
                {
                    "time": 1710003600,
                    "open": 104.0,
                    "high": 110.0,
                    "low": 103.0,
                    "close": 108.0,
                    "volume": 12.0,
                },
            ],
            "meta": {
                "count": 2,
                "from": 1710000000,
                "to": 1710003600,
                "cached": False,
            },
        }


def build_tools(service=None):
    context = SimpleNamespace(
        config=SimpleNamespace(port=6969, cache_ttl_seconds=15),
        authenticator=FakeAuthenticator(),
        service=service or FakeService(),
    )
    return MarketDataMCPTools(context)


class MarketDataMCPToolsTests(unittest.TestCase):
    def test_tv_health_returns_config_and_auth_state(self):
        tools = build_tools()

        payload = tools.tv_health()

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["port"], 6969)
        self.assertEqual(payload["auth"]["mode"], "anonymous")
        self.assertEqual(payload["default_limit"], 500)
        self.assertEqual(payload["max_limit"], 5000)
        self.assertEqual(payload["cache_ttl_seconds"], 15)

    def test_tv_history_maps_arguments_to_market_data_service(self):
        service = FakeService()
        tools = build_tools(service)

        tools.tv_history(
            symbol="BINANCE:BTCUSDT",
            interval="1h",
            limit=250,
            from_ts=1710000000,
            to_ts=1710100000,
            extended_session=True,
        )

        self.assertEqual(
            service.calls[0],
            {
                "symbol": "BINANCE:BTCUSDT",
                "interval": "1h",
                "extended_session": True,
                "limit": 250,
                "from": 1710000000,
                "to": 1710100000,
            },
        )

    def test_tv_history_summary_returns_compact_normal_bar_summary(self):
        tools = build_tools()

        payload = tools.tv_history_summary("BINANCE:BTCUSDT", "1h", limit=2)

        self.assertNotIn("bars", payload)
        self.assertEqual(payload["symbol"], "BINANCE:BTCUSDT")
        self.assertEqual(payload["interval"], "1h")
        self.assertEqual(payload["meta"]["count"], 2)
        self.assertEqual(payload["summary"]["open"], 100.0)
        self.assertEqual(payload["summary"]["high"], 110.0)
        self.assertEqual(payload["summary"]["low"], 99.0)
        self.assertEqual(payload["summary"]["close"], 108.0)
        self.assertEqual(payload["summary"]["volume"], 22.0)
        self.assertEqual(payload["summary"]["change"], 8.0)
        self.assertEqual(payload["summary"]["change_percent"], 8.0)

    def test_tv_history_summary_handles_empty_bars(self):
        service = FakeService(
            [
                {
                    "symbol": "BINANCE:BTCUSDT",
                    "interval": "1h",
                    "timezone": "UTC",
                    "bars": [],
                    "meta": {
                        "count": 0,
                        "from": None,
                        "to": None,
                        "cached": False,
                    },
                }
            ]
        )
        tools = build_tools(service)

        payload = tools.tv_history_summary("BINANCE:BTCUSDT", "1h", limit=2)

        self.assertEqual(payload["meta"]["count"], 0)
        self.assertIsNone(payload["summary"]["open"])
        self.assertIsNone(payload["summary"]["high"])
        self.assertIsNone(payload["summary"]["low"])
        self.assertIsNone(payload["summary"]["close"])
        self.assertEqual(payload["summary"]["volume"], 0.0)
        self.assertIsNone(payload["summary"]["change"])
        self.assertIsNone(payload["summary"]["change_percent"])

    def test_tv_history_multi_returns_compact_result_shape(self):
        service = FakeService()
        tools = build_tools(service)

        payload = tools.tv_history_multi(
            [
                {
                    "symbol": "BINANCE:BTCUSDT",
                    "interval": "1h",
                    "limit": 2,
                },
                {
                    "symbol": "BINANCE:ETHUSDT",
                    "interval": "4h",
                    "from": 1710000000,
                    "to": 1710100000,
                    "extended_session": "false",
                },
            ]
        )

        self.assertEqual(payload["meta"]["count"], 2)
        self.assertEqual(payload["meta"]["max_requests"], 12)
        self.assertEqual(len(payload["results"]), 2)
        self.assertNotIn("bars", payload["results"][0])
        self.assertEqual(payload["results"][0]["symbol"], "BINANCE:BTCUSDT")
        self.assertEqual(payload["results"][1]["symbol"], "BINANCE:ETHUSDT")
        self.assertEqual(service.calls[1]["from"], 1710000000)
        self.assertEqual(service.calls[1]["to"], 1710100000)
        self.assertEqual(service.calls[1]["extended_session"], "false")

    def test_tv_history_multi_rejects_more_than_twelve_requests(self):
        tools = build_tools()

        with self.assertRaises(ValidationError):
            tools.tv_history_multi(
                [
                    {
                        "symbol": "BINANCE:BTCUSDT",
                        "interval": "1h",
                    }
                ]
                * 13
            )


if __name__ == "__main__":
    unittest.main()
