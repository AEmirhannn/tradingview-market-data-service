from typing import Any, Dict

from tradingview_service.cache import SimpleTTLCache
from tradingview_service.client import TradingViewWebSocketClient
from tradingview_service.models import HistoryQuery, build_history_payload


class MarketDataService:
    def __init__(
        self,
        client: TradingViewWebSocketClient,
        cache: SimpleTTLCache,
        *,
        default_limit: int,
        max_limit: int,
    ) -> None:
        self.client = client
        self.cache = cache
        self.default_limit = default_limit
        self.max_limit = max_limit

    def get_history(self, args: Any) -> Dict[str, Any]:
        query = HistoryQuery.from_args(
            args,
            default_limit=self.default_limit,
            max_limit=self.max_limit,
        )
        cache_key = query.cache_key()
        cached_payload = self.cache.get(cache_key)
        if cached_payload is not None:
            payload = dict(cached_payload)
            payload["meta"] = dict(cached_payload["meta"])
            payload["meta"]["cached"] = True
            return payload

        bars = self.client.fetch_history(query)
        payload = build_history_payload(query, bars, cached=False)
        self.cache.set(cache_key, payload)
        return payload
