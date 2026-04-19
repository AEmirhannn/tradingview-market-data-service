# Phase 1 Plan: Market-Data Service Boundary

## Goal

Extract the request orchestration currently embedded in the Flask `/v1/history` handler into a small internal service layer. The public HTTP API and payload shape must remain unchanged.

## Implementation Decisions

- Add an internal service module under `tradingview_service/`.
- Keep `HistoryQuery` validation, `build_history_payload`, `SimpleTTLCache`, and `TradingViewWebSocketClient` behavior unchanged.
- The new service owns:
  - parsing request-like args into `HistoryQuery`
  - cache lookup and cached metadata adjustment
  - client history fetch
  - payload construction
  - cache write
- `create_app` should instantiate the service and store it in `app.config`.
- `/v1/history` should delegate to the service and return `jsonify(payload)`.
- Do not change `/health`, authentication behavior, config defaults, cache TTL, error format, or history response fields.

## Tests

- Add focused unit tests for the new service using fake clients and cache instances.
- Prove uncached history returns the same payload shape as the existing route.
- Prove cached history sets `meta.cached` to `true` without calling the fake client again.
- Keep existing app tests passing without weakening assertions.

## Verification

Run:

```bash
.venv/bin/python -m unittest discover -s tests
```

## Acceptance Criteria

- Existing HTTP behavior is unchanged.
- Existing tests pass.
- New tests do not make live network calls.
- No MCP, CDP, desktop automation, or dependency changes are introduced in this phase.
