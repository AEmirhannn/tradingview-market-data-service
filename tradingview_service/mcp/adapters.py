from dataclasses import dataclass
from typing import Optional

from tradingview_service.auth import TradingViewAuthenticator
from tradingview_service.cache import SimpleTTLCache
from tradingview_service.client import TradingViewWebSocketClient
from tradingview_service.config import AppConfig
from tradingview_service.market_data import MarketDataService
from tradingview_service.runtime import configure_runtime_env


@dataclass(frozen=True)
class MarketDataToolContext:
    config: AppConfig
    authenticator: TradingViewAuthenticator
    client: TradingViewWebSocketClient
    cache: SimpleTTLCache
    service: MarketDataService


def build_market_data_context(config: Optional[AppConfig] = None) -> MarketDataToolContext:
    if config is None:
        configure_runtime_env()
        config = AppConfig.from_env()

    authenticator = TradingViewAuthenticator(
        config.tradingview_username,
        config.tradingview_password,
        timeout_seconds=config.request_timeout_seconds,
    )
    client = TradingViewWebSocketClient(
        authenticator,
        timeout_seconds=config.request_timeout_seconds,
    )
    cache = SimpleTTLCache(config.cache_ttl_seconds)
    service = MarketDataService(
        client,
        cache,
        default_limit=config.default_limit,
        max_limit=config.max_limit,
    )
    return MarketDataToolContext(
        config=config,
        authenticator=authenticator,
        client=client,
        cache=cache,
        service=service,
    )
