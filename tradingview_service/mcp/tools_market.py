from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from tradingview_service.errors import ValidationError
from tradingview_service.mcp.adapters import MarketDataToolContext


MAX_MULTI_HISTORY_REQUESTS = 12


class MarketDataMCPTools:
    def __init__(self, context: MarketDataToolContext) -> None:
        self.context = context

    def tv_health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "port": self.context.config.port,
            "auth": self.context.authenticator.health(),
            "default_limit": self.context.service.default_limit,
            "max_limit": self.context.service.max_limit,
            "cache_ttl_seconds": self.context.config.cache_ttl_seconds,
        }

    def tv_history(
        self,
        symbol: str,
        interval: str,
        limit: Optional[int] = None,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        extended_session: bool = False,
    ) -> Dict[str, Any]:
        return self.context.service.get_history(
            _build_history_args(
                symbol=symbol,
                interval=interval,
                limit=limit,
                from_ts=from_ts,
                to_ts=to_ts,
                extended_session=extended_session,
            )
        )

    def tv_history_summary(
        self,
        symbol: str,
        interval: str,
        limit: Optional[int] = None,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        extended_session: bool = False,
    ) -> Dict[str, Any]:
        payload = self.tv_history(
            symbol=symbol,
            interval=interval,
            limit=limit,
            from_ts=from_ts,
            to_ts=to_ts,
            extended_session=extended_session,
        )
        return summarize_history_payload(payload)

    def tv_history_multi(self, requests: List[Mapping[str, Any]]) -> Dict[str, Any]:
        if not isinstance(requests, list):
            raise ValidationError("requests must be a list")
        if len(requests) > MAX_MULTI_HISTORY_REQUESTS:
            raise ValidationError(
                f"requests must include at most {MAX_MULTI_HISTORY_REQUESTS} symbol/interval entries"
            )

        results = []
        for request in requests:
            if not isinstance(request, Mapping):
                raise ValidationError("each request must be an object")
            results.append(
                self.tv_history_summary(
                    symbol=_required_request_value(request, "symbol"),
                    interval=_required_request_value(request, "interval"),
                    limit=_optional_request_value(request, "limit"),
                    from_ts=_optional_request_value(request, "from_ts", "from"),
                    to_ts=_optional_request_value(request, "to_ts", "to"),
                    extended_session=_optional_request_value(request, "extended_session") or False,
                )
            )

        return {
            "meta": {
                "count": len(results),
                "max_requests": MAX_MULTI_HISTORY_REQUESTS,
            },
            "results": results,
        }


def summarize_history_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    bars = list(payload.get("bars") or [])
    meta = dict(payload.get("meta") or {})

    summary = {
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": 0.0,
        "change": None,
        "change_percent": None,
    }
    if bars:
        first_open = bars[0].get("open")
        last_close = bars[-1].get("close")
        high = max(bar.get("high") for bar in bars)
        low = min(bar.get("low") for bar in bars)
        volume = sum(bar.get("volume") or 0.0 for bar in bars)
        change = last_close - first_open
        change_percent = None if first_open == 0 else (change / first_open) * 100
        summary = {
            "open": first_open,
            "high": high,
            "low": low,
            "close": last_close,
            "volume": volume,
            "change": change,
            "change_percent": change_percent,
        }

    return {
        "symbol": payload.get("symbol"),
        "interval": payload.get("interval"),
        "timezone": payload.get("timezone", "UTC"),
        "meta": meta,
        "summary": summary,
    }


def _build_history_args(
    *,
    symbol: str,
    interval: str,
    limit: Optional[int],
    from_ts: Optional[int],
    to_ts: Optional[int],
    extended_session: bool,
) -> Dict[str, Any]:
    args: Dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "extended_session": extended_session,
    }
    if limit is not None:
        args["limit"] = limit
    if from_ts is not None:
        args["from"] = from_ts
    if to_ts is not None:
        args["to"] = to_ts
    return args


def _required_request_value(request: Mapping[str, Any], key: str) -> Any:
    value = request.get(key)
    if value is None or str(value).strip() == "":
        raise ValidationError(f"each request requires {key}")
    return value


def _optional_request_value(request: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = request.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return None
