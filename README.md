# TradingView Market Data Service

Local Flask and MCP service for fetching historical TradingView OHLCV bars for AI agents, research tools, and automation workflows.

The current release includes:

- A REST API for historical OHLCV retrieval.
- An in-process market-data service layer shared by Flask and MCP.
- A stdio MCP server with market-data tools.
- Anonymous TradingView access by default, with optional credentialed mode.

TradingView Desktop chart automation and visible chart annotation are planned but not implemented yet. See [FEATURE_PLAN.md](FEATURE_PLAN.md) for the roadmap.

## What It Provides

REST endpoints:

- `GET /health`
- `GET /v1/history?symbol=BINANCE:BTCUSDT&interval=1h&limit=5000`

MCP tools:

- `tv_health`
- `tv_history`
- `tv_history_summary`
- `tv_history_multi`

The service accepts full TradingView symbols such as `BINANCE:BTCUSDT` and `NASDAQ:AAPL`. Supported intervals are `1m`, `3m`, `5m`, `15m`, `30m`, `45m`, `1h`, `2h`, `3h`, `4h`, `1d`, `1w`, and `1M`.

## Project Status

The current implementation is the Phase 2 MCP MVP:

- The Flask service is the stable historical-data API.
- The MCP server calls the same in-process market-data service; it does not call the local Flask HTTP API.
- REST and MCP use one Python 3.12 virtual environment.
- No CDP, TradingView Desktop control, screenshots, Pine tools, or chart annotations are included in this release.

Safety boundaries for future work:

- Desktop automation must be opt-in and localhost-only.
- Trade execution is out of scope.
- Broad arbitrary UI automation is out of scope for the MVP.
- Agent-created chart drawings must be tagged and removable without touching user-created drawings.
- Any new TradingView-hosted upstream calls must be documented before they are introduced.

## REST Service Setup

Create a Python 3.12 virtual environment and install dependencies:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run the service:

```bash
.venv/bin/python run.py
```

Default port: `6969`

Example request:

```bash
curl -fsS -G "http://127.0.0.1:6969/v1/history" \
  --data-urlencode "symbol=BINANCE:BTCUSDT" \
  --data-urlencode "interval=1h" \
  --data-urlencode "limit=500"
```

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

## MCP Server Setup

Run the MCP server over stdio from the repository root:

```bash
.venv/bin/python -m tradingview_service.mcp.server
```

Example MCP client config:

```json
{
  "mcpServers": {
    "tradingview-marketdata": {
      "command": "/absolute/path/to/tradingview-market-data-service/.venv/bin/python",
      "args": ["-m", "tradingview_service.mcp.server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/tradingview-market-data-service"
      }
    }
  }
}
```

Replace `/absolute/path/to/tradingview-market-data-service` with the absolute path to your local checkout.

Smoke-test the MCP server:

```bash
.venv/bin/python scripts/check_mcp.py
```

The smoke script lists registered tools, calls `tv_health`, and calls `tv_history_multi` with a one-bar daily `BINANCE:BTCUSDT` request. Use `--symbol`, `--interval`, and `--limit` to override that request.

## MCP Tool Behavior

`tv_health` returns service status, configured port, auth health, default limit, max limit, and cache TTL.

`tv_history` returns full OHLCV bars for one symbol and interval.

`tv_history_summary` returns a compact OHLCV summary for one symbol and interval.

`tv_history_multi` returns compact summaries for up to 12 symbol/interval requests. Multi-history output intentionally omits full bars to keep agent context usage bounded.

All history tools use full TradingView symbols and the supported interval values listed above. Optional time bounds use `from_ts` and `to_ts` Unix timestamps. Multi-history request objects may also use `from` and `to` for compatibility with the REST query names.

## Authentication Mode

The service starts in anonymous mode by default. This avoids credential login issues and is the recommended default for local AI tooling.

To explicitly enable TradingView login:

```bash
TRADINGVIEW_USE_CREDENTIALS=1
TRADINGVIEW_USERNAME=your_username
TRADINGVIEW_PASSWORD=your_password
```

Do not commit `.env` or real TradingView credentials.

## Notes

- TradingView's unofficial websocket flow effectively limits deep history retrieval to roughly `5000` bars per request path used here.
- If a requested window is older than the reachable backfill range, the service returns a validation error instead of silent partial data.
- This project is not affiliated with, endorsed by, or associated with TradingView Inc.
