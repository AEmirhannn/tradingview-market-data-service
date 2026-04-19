# Phase 2 Plan: MCP Server MVP

## Goal

Add a minimal MCP server for market-data access while keeping the existing Flask service and Python 3.9 development path intact.

## Dependency Decision

- Use the official Python `mcp` package, pinned in a new `requirements-mcp.txt`.
- Pin `mcp==1.27.0`.
- Do not add `mcp` to `requirements.txt` because the current project venv is Python 3.9 and `mcp` requires Python `>=3.10`.
- Document MCP setup with a Python 3.10+ environment, preferably Python 3.12 where available.

## Runtime Decision

- MCP tools call in-process Python services by default.
- Do not call the local Flask HTTP API from MCP tools in this phase.
- Do not add CDP, TradingView Desktop automation, screenshots, chart control, or annotation tools.

## Implementation Decisions

- Add `tradingview_service/mcp/`.
- Keep FastMCP server registration isolated in `server.py`.
- Keep tool behavior testable without importing the `mcp` dependency by placing pure tool helpers in a separate module.
- Add an adapter that builds `AppConfig`, `TradingViewAuthenticator`, `TradingViewWebSocketClient`, `SimpleTTLCache`, and `MarketDataService`.
- Expose these tools:
  - `tv_health`: returns service status, configured port, auth health, default limit, max limit, and cache TTL.
  - `tv_history`: returns the normal history payload for one symbol and interval.
  - `tv_history_summary`: returns compact OHLCV summary for one symbol and interval.
  - `tv_history_multi`: returns compact summaries for a bounded set of symbol/interval combinations.
- Keep full bar output available only through `tv_history`; multi requests must use summaries.
- Bound `tv_history_multi` to at most 12 symbol/interval requests per call.

## Tests

- Add fake-based tests for tool helper behavior.
- Test `tv_history` argument mapping to `MarketDataService`.
- Test summary calculations for normal bars and empty bars.
- Test multi-request bounding and result shape.
- Do not require a live TradingView network call.

## Verification

Run the existing suite:

```bash
.venv/bin/python -m unittest discover -s tests
```

Run MCP dependency verification with Python 3.10+:

```bash
python3.12 -m venv /tmp/marketdata-mcp-venv
/tmp/marketdata-mcp-venv/bin/python -m pip install -r requirements.txt -r requirements-mcp.txt
/tmp/marketdata-mcp-venv/bin/python -m unittest discover -s tests
/tmp/marketdata-mcp-venv/bin/python -c "from tradingview_service.mcp.server import create_server; create_server()"
```

## Acceptance Criteria

- Existing Flask service tests still pass in the current `.venv`.
- MCP code can be imported with Python 3.10+ after installing `requirements-mcp.txt`.
- MCP tools do not require TradingView Desktop or CDP.
- README includes setup and MCP config examples.
