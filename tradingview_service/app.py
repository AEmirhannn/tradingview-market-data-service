import logging
from typing import Optional

from flask import Flask, jsonify, request

from tradingview_service.auth import TradingViewAuthenticator
from tradingview_service.cache import SimpleTTLCache
from tradingview_service.client import TradingViewWebSocketClient
from tradingview_service.config import AppConfig
from tradingview_service.errors import AppError
from tradingview_service.market_data import MarketDataService


def create_app(
    config: Optional[AppConfig] = None,
    *,
    tv_client: Optional[TradingViewWebSocketClient] = None,
    cache: Optional[SimpleTTLCache] = None,
) -> Flask:
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()

    logging.basicConfig(level=getattr(logging, app_config.log_level, logging.INFO))

    authenticator = TradingViewAuthenticator(
        app_config.tradingview_username,
        app_config.tradingview_password,
        timeout_seconds=app_config.request_timeout_seconds,
    )
    history_client = tv_client or TradingViewWebSocketClient(
        authenticator,
        timeout_seconds=app_config.request_timeout_seconds,
    )
    history_cache = cache or SimpleTTLCache(app_config.cache_ttl_seconds)
    market_data_service = MarketDataService(
        history_client,
        history_cache,
        default_limit=app_config.default_limit,
        max_limit=app_config.max_limit,
    )

    app.config["APP_CONFIG"] = app_config
    app.config["AUTHENTICATOR"] = authenticator
    app.config["HISTORY_CLIENT"] = history_client
    app.config["HISTORY_CACHE"] = history_cache
    app.config["MARKET_DATA_SERVICE"] = market_data_service

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("unhandled error: %s", error)
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "unexpected server error"}}), 500

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "port": app_config.port,
                "auth": authenticator.health(),
            }
        )

    @app.get("/v1/history")
    def history():
        return jsonify(market_data_service.get_history(request.args))

    return app
