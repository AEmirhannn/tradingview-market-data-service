# TradingView Market Data Service

Backend Flask service that fetches TradingView chart data and exposes historical OHLCV bars over a simple REST API. This project is intended as a local market-data backend for AI agents, skills, and automation that need clean access to chart history.

## What It Provides

- `GET /health`
- `GET /v1/history?symbol=BINANCE:BTCUSDT&interval=1h&limit=5000`

The service accepts full TradingView symbols such as `BINANCE:BTCUSDT` and `NASDAQ:AAPL`. Supported intervals are `1m,3m,5m,15m,30m,45m,1h,2h,3h,4h,1d,1w,1M`.

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

Skills for consuming this service should be created by the repository user in their own local Codex skill directory. Do not assume a shared skill is already installed.

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
