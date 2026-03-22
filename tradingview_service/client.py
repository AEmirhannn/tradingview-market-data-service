import json
import random
import re
import string
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from websocket import create_connection

from tradingview_service.auth import TradingViewAuthenticator
from tradingview_service.errors import AuthenticationError, UpstreamError
from tradingview_service.models import Bar, HistoryQuery, filter_bars


HEARTBEAT_RE = re.compile(r"~m~\d+~m~~h~\d+")
PAYLOAD_SPLIT_RE = re.compile(r"~m~\d+~m~")


class TradingViewWebSocketClient:
    WS_URL = "wss://data.tradingview.com/socket.io/websocket"
    ORIGIN_HEADER = "Origin: https://www.tradingview.com"

    def __init__(
        self,
        authenticator: TradingViewAuthenticator,
        *,
        timeout_seconds: int,
        ws_factory=create_connection,
    ) -> None:
        self.authenticator = authenticator
        self.timeout_seconds = timeout_seconds
        self.ws_factory = ws_factory

    def fetch_history(self, query: HistoryQuery) -> List[Bar]:
        token = self.authenticator.get_token()
        try:
            return self._fetch_history(query, token=token)
        except AuthenticationError:
            refreshed = self.authenticator.get_token(force_refresh=True)
            return self._fetch_history(query, token=refreshed)

    def _fetch_history(self, query: HistoryQuery, *, token: str) -> List[Bar]:
        chart_session = self._generate_session("cs")
        series_name = "s1"
        bars: List[Bar] = []
        ws = None
        unauthorized = False
        last_error: Optional[str] = None

        try:
            ws = self.ws_factory(
                self.WS_URL,
                header=[self.ORIGIN_HEADER],
                timeout=self.timeout_seconds,
            )

            self._prime_socket(ws)
            self._send_message(ws, "set_data_quality", ["low"])
            self._send_message(ws, "set_auth_token", [token])
            self._send_message(ws, "chart_create_session", [chart_session, ""])
            self._send_message(
                ws,
                "resolve_symbol",
                [
                    chart_session,
                    "symbol_1",
                    self._build_symbol_payload(query.symbol, extended_session=query.extended_session),
                ],
            )
            self._send_message(
                ws,
                "create_series",
                [
                    chart_session,
                    series_name,
                    series_name,
                    "symbol_1",
                    query.tv_interval,
                    query.bars_to_request(now_ts=int(time.time())),
                ],
            )
            self._send_message(ws, "switch_timezone", [chart_session, "Etc/UTC"])

            deadline = time.time() + self.timeout_seconds
            while time.time() < deadline:
                try:
                    raw_frame = ws.recv()
                except Exception as exc:
                    raise UpstreamError("failed while reading from TradingView websocket") from exc
                for heartbeat in HEARTBEAT_RE.findall(raw_frame):
                    ws.send(self._prepend_message(heartbeat))

                for payload in self._decode_payloads(raw_frame):
                    message_type = payload.get("m")

                    if message_type in {"error", "critical_error", "symbol_error", "series_error"}:
                        last_error = self._extract_error(payload)
                        if "auth" in last_error.lower() or "permission" in last_error.lower():
                            unauthorized = True
                        raise AuthenticationError(last_error) if unauthorized else UpstreamError(last_error)

                    if message_type == "timescale_update":
                        bars = self._extract_bars(payload, series_name)
                        continue

                    if message_type == "du":
                        candidate = self._extract_bars(payload, series_name)
                        if candidate:
                            bars = candidate
                        continue

                    if message_type == "series_completed":
                        filtered = filter_bars(bars, query)
                        if filtered:
                            return filtered
                        if bars:
                            raise UpstreamError("no bars remain after applying the requested range")
                        break

                if bars and query.from_ts is None and query.to_ts is None:
                    return filter_bars(bars, query)

            if unauthorized:
                raise AuthenticationError(last_error or "TradingView rejected the current auth token")
            if last_error:
                raise UpstreamError(last_error)
            if bars:
                return filter_bars(bars, query)
            raise UpstreamError("TradingView returned no historical data")
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    def _prime_socket(self, ws: Any) -> None:
        try:
            initial_frame = ws.recv()
        except Exception as exc:
            raise UpstreamError("failed to initialize TradingView websocket") from exc

        for heartbeat in HEARTBEAT_RE.findall(initial_frame):
            ws.send(self._prepend_message(heartbeat))

    @staticmethod
    def _build_symbol_payload(symbol: str, *, extended_session: bool) -> str:
        payload = {
            "symbol": symbol,
            "adjustment": "splits",
            "session": "extended" if extended_session else "regular",
        }
        return "=" + json.dumps(payload, separators=(",", ":"))

    @staticmethod
    def _generate_session(prefix: str) -> str:
        suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        return f"{prefix}_{suffix}"

    @staticmethod
    def _construct_message(name: str, params: Sequence[Any]) -> str:
        return json.dumps({"m": name, "p": list(params)}, separators=(",", ":"))

    @classmethod
    def _prepend_message(cls, payload: str) -> str:
        return f"~m~{len(payload)}~m~{payload}"

    @classmethod
    def _send_message(cls, ws: Any, name: str, params: Sequence[Any]) -> None:
        ws.send(cls._prepend_message(cls._construct_message(name, params)))

    @staticmethod
    def _decode_payloads(frame: str) -> List[Dict[str, Any]]:
        decoded: List[Dict[str, Any]] = []
        for chunk in PAYLOAD_SPLIT_RE.split(frame):
            chunk = chunk.strip()
            if not chunk or chunk.startswith("~h~"):
                continue
            try:
                decoded.append(json.loads(chunk))
            except json.JSONDecodeError:
                continue
        return decoded

    @staticmethod
    def _extract_error(payload: Dict[str, Any]) -> str:
        params = payload.get("p", [])
        if not params:
            return "TradingView returned an unspecified error"
        if isinstance(params[-1], str):
            return params[-1]
        return json.dumps(params[-1], separators=(",", ":"))

    @staticmethod
    def _extract_bars(payload: Dict[str, Any], series_name: str) -> List[Bar]:
        params = payload.get("p", [])
        if len(params) < 2 or not isinstance(params[1], dict):
            return []

        series = params[1].get(series_name)
        if not isinstance(series, dict):
            return []

        rows = series.get("s", [])
        bars: List[Bar] = []
        for row in rows:
            values = row.get("v", [])
            if len(values) < 5:
                continue
            volume = float(values[5]) if len(values) > 5 and values[5] is not None else 0.0
            bars.append(
                Bar(
                    time=int(values[0]),
                    open=float(values[1]),
                    high=float(values[2]),
                    low=float(values[3]),
                    close=float(values[4]),
                    volume=volume,
                )
            )
        return bars
