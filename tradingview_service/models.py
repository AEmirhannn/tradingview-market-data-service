import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from tradingview_service.errors import ValidationError


INTERVAL_MAP = {
    "1m": ("1", 60),
    "3m": ("3", 180),
    "5m": ("5", 300),
    "15m": ("15", 900),
    "30m": ("30", 1800),
    "45m": ("45", 2700),
    "1h": ("1H", 3600),
    "2h": ("2H", 7200),
    "3h": ("3H", 10800),
    "4h": ("4H", 14400),
    "1d": ("1D", 86400),
    "1w": ("1W", 604800),
    "1M": ("1M", 2592000),
}


@dataclass(frozen=True)
class Bar:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoryQuery:
    symbol: str
    interval: str
    tv_interval: str
    interval_seconds: int
    limit: int
    from_ts: Optional[int]
    to_ts: Optional[int]
    extended_session: bool

    @classmethod
    def from_args(
        cls,
        args: Any,
        *,
        default_limit: int,
        max_limit: int,
        now_ts: Optional[int] = None,
    ) -> "HistoryQuery":
        now_ts = now_ts or int(time.time())

        symbol = (args.get("symbol") or "").strip()
        if not symbol or ":" not in symbol:
            raise ValidationError("symbol is required and must be a full TradingView symbol like BINANCE:BTCUSDT")

        interval = (args.get("interval") or "").strip()
        interval_config = INTERVAL_MAP.get(interval)
        if interval_config is None:
            raise ValidationError(f"interval must be one of: {', '.join(INTERVAL_MAP.keys())}")

        limit_raw = args.get("limit")
        if limit_raw is None or str(limit_raw).strip() == "":
            limit = default_limit
        else:
            limit = _parse_positive_int("limit", limit_raw)

        if limit > max_limit:
            raise ValidationError(f"limit must be <= {max_limit}")

        from_ts = _parse_optional_int("from", args.get("from"))
        to_ts = _parse_optional_int("to", args.get("to"))
        if from_ts is not None and to_ts is not None and from_ts > to_ts:
            raise ValidationError("from must be <= to")

        extended_session = _parse_bool(args.get("extended_session", "false"))

        query = cls(
            symbol=symbol,
            interval=interval,
            tv_interval=interval_config[0],
            interval_seconds=interval_config[1],
            limit=limit,
            from_ts=from_ts,
            to_ts=to_ts,
            extended_session=extended_session,
        )
        query.validate_range_depth(now_ts=now_ts, max_limit=max_limit)
        return query

    def cache_key(self) -> Tuple[Any, ...]:
        return (
            self.symbol,
            self.interval,
            self.limit,
            self.from_ts,
            self.to_ts,
            self.extended_session,
        )

    def bars_to_request(self, *, now_ts: Optional[int] = None) -> int:
        now_ts = now_ts or int(time.time())

        if self.from_ts is None and self.to_ts is None:
            return self.limit

        if self.from_ts is not None:
            earliest = self.from_ts
        elif self.to_ts is not None:
            earliest = self.to_ts - ((self.limit - 1) * self.interval_seconds)
        else:
            earliest = now_ts

        if earliest > now_ts:
            return self.limit

        bars_back = math.ceil((now_ts - earliest) / self.interval_seconds) + 2
        return max(self.limit, bars_back)

    def validate_range_depth(self, *, now_ts: int, max_limit: int) -> None:
        required_bars = self.bars_to_request(now_ts=now_ts)
        if required_bars > max_limit:
            raise ValidationError(
                "requested history window is too deep for this interval; "
                f"it would require {required_bars} bars while the service limit is {max_limit}"
            )


def filter_bars(bars: List[Bar], query: HistoryQuery) -> List[Bar]:
    filtered = bars
    if query.from_ts is not None:
        filtered = [bar for bar in filtered if bar.time >= query.from_ts]
    if query.to_ts is not None:
        filtered = [bar for bar in filtered if bar.time <= query.to_ts]
    if len(filtered) > query.limit:
        filtered = filtered[-query.limit :]
    return filtered


def build_history_payload(query: HistoryQuery, bars: List[Bar], *, cached: bool) -> Dict[str, Any]:
    payload_bars = [bar.to_dict() for bar in bars]
    return {
        "symbol": query.symbol,
        "interval": query.interval,
        "timezone": "UTC",
        "bars": payload_bars,
        "meta": {
            "count": len(payload_bars),
            "from": payload_bars[0]["time"] if payload_bars else None,
            "to": payload_bars[-1]["time"] if payload_bars else None,
            "cached": cached,
        },
    }


def _parse_positive_int(name: str, value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be an integer")
    if parsed <= 0:
        raise ValidationError(f"{name} must be > 0")
    return parsed


def _parse_optional_int(name: str, value: Any) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    return _parse_positive_int(name, value)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValidationError("extended_session must be a boolean")

