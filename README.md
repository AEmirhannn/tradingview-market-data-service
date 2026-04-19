# TradingView Market Data Service

Backend Flask service that fetches TradingView chart data and exposes historical OHLCV bars over a simple REST API. This project is intended as a local market-data backend for AI agents, skills, and automation that need clean access to chart history.

## What It Provides

- `GET /health`
- `GET /v1/history?symbol=BINANCE:BTCUSDT&interval=1h&limit=5000`

The service accepts full TradingView symbols such as `BINANCE:BTCUSDT` and `NASDAQ:AAPL`. Supported intervals are `1m,3m,5m,15m,30m,45m,1h,2h,3h,4h,1d,1w,1M`.

## Roadmap: MCP and Chart Annotation

This project is planned to grow into a local TradingView MarketData MCP toolchain. The existing Flask service remains the reliable market-data core for historical OHLCV retrieval, validation, caching, and agent-friendly API access.

The next major layers are:

- An MCP server that exposes market-data tools, compact history summaries, and multi-symbol or multi-timeframe requests.
- Local technical-analysis helpers that run over fetched OHLCV data without depending on a visible chart.
- Optional TradingView Desktop automation through Chrome DevTools Protocol for chart state, screenshots, and visible annotations.

Desktop automation must stay opt-in and localhost-only. The project will not add trade execution, credential harvesting, remote CDP access, or broad arbitrary UI automation as part of the MVP. Agent-created drawings must be tagged so they can be removed without touching user-created chart objects.

No MCP or CDP dependency is required for the current service. Future MCP and desktop-control libraries should be added only in the smallest implementation commit that uses them. Any new TradingView-hosted upstream calls must be documented before they are introduced.

See [FEATURE_PLAN.md](FEATURE_PLAN.md) for the step-by-step implementation roadmap.

## Local Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/python run.py
```

Default port: `6969`

Run tests with:

```bash
.venv/bin/python -m unittest discover -s tests
```

## MCP Server

The MCP server exposes the existing in-process market-data service over stdio. It does not call the local Flask HTTP API, and this MVP does not include TradingView Desktop automation, CDP, screenshots, chart control, Pine tools, or annotation tools.

The MCP dependency is intentionally separate from `requirements.txt` because the current service venv can run on Python 3.9 while `mcp` requires Python 3.10 or newer. Use a separate Python 3.10+ environment for MCP, preferably Python 3.12 where available:

```bash
/opt/homebrew/bin/python3.12 -m venv /tmp/marketdata-mcp-venv
/tmp/marketdata-mcp-venv/bin/python -m pip install -r requirements.txt -r requirements-mcp.txt
/tmp/marketdata-mcp-venv/bin/python -c "from tradingview_service.mcp.server import create_server; create_server()"
```

Run the MCP server over stdio with:

```bash
PYTHONPATH=/Users/aemirhan/Desktop/Projects/marketData \
  /tmp/marketdata-mcp-venv/bin/python -m tradingview_service.mcp.server
```

Available tools:

- `tv_health`: returns service status, configured port, auth health, default limit, max limit, and cache TTL.
- `tv_history`: returns full OHLCV bars for one symbol and interval.
- `tv_history_summary`: returns a compact OHLCV summary for one symbol and interval.
- `tv_history_multi`: returns compact summaries for up to 12 symbol/interval requests.

`tv_history`, `tv_history_summary`, and each `tv_history_multi` request use full TradingView symbols and supported intervals. Optional time bounds are `from_ts` and `to_ts` Unix timestamps. Multi-history requests may also use `from` and `to` inside each request object for compatibility with the Flask query names.

Example MCP client config:

```json
{
  "mcpServers": {
    "tradingview-marketdata": {
      "command": "/tmp/marketdata-mcp-venv/bin/python",
      "args": ["-m", "tradingview_service.mcp.server"],
      "env": {
        "PYTHONPATH": "/Users/aemirhan/Desktop/Projects/marketData"
      }
    }
  }
}
```

## Authentication Mode

The service starts in anonymous mode by default. That avoids credential login issues and is the recommended default for local AI tooling.

To explicitly enable TradingView login:

```bash
TRADINGVIEW_USE_CREDENTIALS=1
TRADINGVIEW_USERNAME=your_username
TRADINGVIEW_PASSWORD=your_password
```

Never commit `.env` or real account credentials.

## Using This From AI Skills

Skills for consuming this service should be created by the repository user in their own local Agents skill directory. Do not assume a shared skill is already installed.

My recommended setup is exactly what I use locally: create user-owned `curl` helper scripts that accept arguments and call this backend. Mention those scripts in the skill instructions so the agent uses them instead of hand-writing requests each time.

Typical examples:

```bash
scripts/fetch_history.sh BINANCE:BTCUSDT 4h
scripts/fetch_max_history.sh BINANCE:ETHUSDT
```

Example `curl` pattern for a helper script:

```bash
curl -fsS -G "http://127.0.0.1:6969/v1/history" \
  --data-urlencode "symbol=${SYMBOL}" \
  --data-urlencode "interval=${INTERVAL}" \
  --data-urlencode "limit=${LIMIT:-5000}"
```

That setup keeps the service generic while letting each user define their own local AI skill, preferred scripts, symbols, and workflows.

## Notes

- TradingView's unofficial websocket flow effectively limits deep history retrieval to roughly `5000` bars per request path used here.
- If a requested window is older than the reachable backfill range, the service returns a validation error instead of silent partial data.
