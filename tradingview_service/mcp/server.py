from typing import Any, Dict, List, Optional

from tradingview_service.mcp.adapters import MarketDataToolContext, build_market_data_context
from tradingview_service.mcp.tools_market import MarketDataMCPTools


def create_server(context: Optional[MarketDataToolContext] = None) -> Any:
    from mcp.server.fastmcp import FastMCP

    tool_context = context or build_market_data_context()
    tools = MarketDataMCPTools(tool_context)
    server = FastMCP("TradingView MarketData")

    @server.tool()
    def tv_health() -> Dict[str, Any]:
        """Return local market-data service status and runtime configuration."""
        return tools.tv_health()

    @server.tool()
    def tv_history(
        symbol: str,
        interval: str,
        limit: Optional[int] = None,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        extended_session: bool = False,
    ) -> Dict[str, Any]:
        """Return full OHLCV bars for one TradingView symbol and interval."""
        return tools.tv_history(
            symbol=symbol,
            interval=interval,
            limit=limit,
            from_ts=from_ts,
            to_ts=to_ts,
            extended_session=extended_session,
        )

    @server.tool()
    def tv_history_summary(
        symbol: str,
        interval: str,
        limit: Optional[int] = None,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        extended_session: bool = False,
    ) -> Dict[str, Any]:
        """Return a compact OHLCV summary for one TradingView symbol and interval."""
        return tools.tv_history_summary(
            symbol=symbol,
            interval=interval,
            limit=limit,
            from_ts=from_ts,
            to_ts=to_ts,
            extended_session=extended_session,
        )

    @server.tool()
    def tv_history_multi(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return compact summaries for up to 12 symbol/interval requests."""
        return tools.tv_history_multi(requests)

    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
