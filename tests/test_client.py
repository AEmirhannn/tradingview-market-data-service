import unittest

from tradingview_service.auth import TradingViewAuthenticator
from tradingview_service.client import TradingViewWebSocketClient
from tradingview_service.errors import UpstreamError
from tradingview_service.models import HistoryQuery


class FakeWebSocket:
    def __init__(self, frames):
        self.frames = list(frames)
        self.sent = []
        self.closed = False

    def recv(self):
        if not self.frames:
            raise AssertionError("no more frames available")
        return self.frames.pop(0)

    def send(self, payload):
        self.sent.append(payload)

    def close(self):
        self.closed = True


class ClientTests(unittest.TestCase):
    def test_decode_payloads_ignores_heartbeats(self):
        frame = '~m~4~m~~h~1~m~27~m~{"m":"series_completed","p":[]}'
        payloads = TradingViewWebSocketClient._decode_payloads(frame)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["m"], "series_completed")

    def test_fetch_history_parses_timescale_update(self):
        frames = [
            "~m~4~m~~h~1",
            (
                '~m~118~m~{"m":"timescale_update","p":["cs_test",{"s1":{"s":['
                '{"i":0,"v":[1710000000,1,2,0.5,1.5,10]},'
                '{"i":1,"v":[1710000060,1.5,2.5,1,2,11]}]}}]}'
                '~m~32~m~{"m":"series_completed","p":[]}'
            ),
        ]
        fake_socket = FakeWebSocket(frames)
        auth = TradingViewAuthenticator("", "", timeout_seconds=5)
        client = TradingViewWebSocketClient(
            auth,
            timeout_seconds=5,
            ws_factory=lambda *args, **kwargs: fake_socket,
        )
        query = HistoryQuery.from_args(
            {"symbol": "BINANCE:BTCUSDT", "interval": "1m", "limit": "2"},
            default_limit=500,
            max_limit=5000,
            now_ts=1710000100,
        )
        bars = client.fetch_history(query)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0].time, 1710000000)
        self.assertEqual(bars[1].close, 2.0)
        self.assertTrue(fake_socket.closed)

    def test_fetch_history_raises_on_symbol_error(self):
        frames = [
            "~m~4~m~~h~1",
            '~m~86~m~{"m":"symbol_error","p":["cs_test","symbol_1","invalid symbol"]}',
        ]
        fake_socket = FakeWebSocket(frames)
        auth = TradingViewAuthenticator("", "", timeout_seconds=5)
        client = TradingViewWebSocketClient(
            auth,
            timeout_seconds=5,
            ws_factory=lambda *args, **kwargs: fake_socket,
        )
        query = HistoryQuery.from_args(
            {"symbol": "BINANCE:XAUTUSD", "interval": "1m", "limit": "2"},
            default_limit=500,
            max_limit=5000,
            now_ts=1710000100,
        )
        with self.assertRaises(UpstreamError):
            client.fetch_history(query)
        self.assertTrue(fake_socket.closed)


if __name__ == "__main__":
    unittest.main()
