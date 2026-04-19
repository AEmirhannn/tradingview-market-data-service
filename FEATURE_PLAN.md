# TradingView MarketData MCP Feature Plan

This document tracks the incremental path from the current Flask market-data service to a local MCP server with TradingView Desktop chart annotation. Keep each step small enough to land as an isolated commit with tests or clear manual verification.

## Product Goal

Build a reliable local toolchain that lets AI agents:

- Fetch clean historical TradingView OHLCV data through the existing market-data logic.
- Run deterministic technical-analysis helpers over that data.
- Optionally connect to the user's local TradingView Desktop app through Chrome DevTools Protocol.
- Draw analysis artifacts on the visible chart so the user can inspect the agent's work.

The project should stay focused on market analysis and chart annotation. Trade execution, credential harvesting, remote CDP access, and broad arbitrary UI control are out of scope unless explicitly added later with separate safeguards.

## Design Principles

- Keep market-data logic independent from desktop automation.
- Prefer small, typed, testable modules over large tool handlers.
- Use the existing Flask API and websocket client behavior as the reliability baseline.
- Make MCP tools thin adapters over internal Python services.
- Keep dangerous desktop features opt-in and localhost-only.
- Return compact summaries by default; require explicit options for large bar payloads.
- Tag all agent-created chart drawings so they can be cleaned up safely.
- Document every upstream TradingView interaction honestly.

## Target Architecture

```text
tradingview_service/
  analysis/
    technical.py
    summaries.py
  desktop/
    connection.py
    chart.py
    drawing.py
    capture.py
    safety.py
  mcp/
    server.py
    tools_market.py
    tools_analysis.py
    tools_desktop.py
    tools_annotation.py
    schemas.py
    adapters.py
```

## Phase 0: Planning and Guardrails

- [x] Create this feature plan.
- [x] Add README section describing the intended MCP and desktop-annotation roadmap.
- [x] Add dependency policy for MCP and CDP libraries before implementation.
- [ ] Decide whether MCP runs in-process against Python services or calls the local Flask API by default.

Suggested commits:

1. `Add TradingView MCP feature plan`
2. `Document MCP roadmap and safety boundaries`

Acceptance criteria:

- The roadmap is discoverable from the repo root.
- The out-of-scope boundaries are explicit before code is added.

## Phase 1: Internal Market-Data Service Boundary

- [ ] Add a service module that wraps `TradingViewWebSocketClient.fetch_history`.
- [ ] Keep the Flask route as a caller of this service instead of owning orchestration directly.
- [ ] Add tests proving the service returns the same payload shape as `/v1/history`.
- [ ] Preserve current cache behavior and validation semantics.

Suggested commit:

1. `Extract market data service layer`

Acceptance criteria:

- Existing HTTP behavior is unchanged.
- Existing tests pass.
- New service tests use fakes rather than live network calls.

## Phase 2: MCP Server MVP

- [ ] Add a Python MCP dependency after choosing the library.
- [ ] Create `tradingview_service/mcp/server.py`.
- [ ] Add `tv_health`.
- [ ] Add `tv_history`.
- [ ] Add `tv_history_summary`.
- [ ] Add `tv_history_multi` for bounded multi-symbol or multi-timeframe requests.
- [ ] Add tests for tool handlers using fake market-data services.
- [ ] Add sample MCP config to README.

Suggested commits:

1. `Add MCP server skeleton`
2. `Add MCP market data tools`
3. `Document MCP setup`

Acceptance criteria:

- MCP server starts over stdio.
- Tools can be exercised without a live TradingView Desktop app.
- Large OHLCV output is opt-in or bounded.

## Phase 3: Technical-Analysis Helpers

- [ ] Add `analysis/technical.py` with pure functions for common calculations.
- [ ] Implement swing high/low detection.
- [ ] Implement support/resistance level clustering.
- [ ] Implement ATR and volatility summary.
- [ ] Implement trend summary from moving averages or regression slope.
- [ ] Add `analysis/summaries.py` for compact agent-facing output.
- [ ] Add deterministic tests with fixed bar fixtures.

Suggested commits:

1. `Add technical analysis primitives`
2. `Add market summary generation`
3. `Expose analysis tools through MCP`

Acceptance criteria:

- Analysis functions are pure and do not call TradingView.
- Tests cover edge cases: empty bars, too few bars, flat markets, noisy levels.
- MCP analysis output stays compact and includes enough evidence for user review.

## Phase 4: Desktop CDP Connection Foundation

- [ ] Add `desktop/safety.py` with localhost-only checks and input sanitation helpers.
- [ ] Add `desktop/connection.py` for Chrome DevTools Protocol connection management.
- [ ] Add `tv_desktop_health`.
- [ ] Add `tv_chart_state`.
- [ ] Add tests around URL/host validation and JavaScript string escaping.
- [ ] Add manual verification instructions for launching TradingView Desktop with `--remote-debugging-port=9222`.

Suggested commits:

1. `Add desktop safety helpers`
2. `Add TradingView Desktop CDP connection`
3. `Expose desktop health MCP tools`

Acceptance criteria:

- CDP connects only to `localhost` or `127.0.0.1`.
- Failures produce clear errors when TradingView is not running.
- No arbitrary JavaScript evaluation tool is exposed in the MVP.

## Phase 5: Chart Control MVP

- [ ] Add `desktop/chart.py`.
- [ ] Implement get current symbol/timeframe/chart type.
- [ ] Implement set symbol.
- [ ] Implement set timeframe.
- [ ] Add MCP tools: `tv_chart_set_symbol`, `tv_chart_set_timeframe`.
- [ ] Add manual verification checklist because these tools require a live desktop app.

Suggested commit:

1. `Add basic TradingView chart control`

Acceptance criteria:

- Tool results include requested state and observed state after the action.
- Tool handlers sanitize symbol and timeframe inputs.
- Manual verification confirms the visible chart changes as expected.

## Phase 6: Screenshot and Visual Evidence

- [ ] Add `desktop/capture.py`.
- [ ] Implement full-window screenshot.
- [ ] Implement chart-area screenshot if a stable selector can be found.
- [ ] Save screenshots to a predictable local output directory ignored by git.
- [ ] Add MCP tool: `tv_screenshot`.
- [ ] Document where screenshots are written.

Suggested commit:

1. `Add TradingView screenshot capture`

Acceptance criteria:

- Screenshot files are created locally and not committed.
- Tool output returns file path and capture metadata.
- Failure mode is clear when TradingView is not connected.

## Phase 7: Drawing and Annotation Primitives

- [ ] Add `desktop/drawing.py`.
- [ ] Implement horizontal line drawing.
- [ ] Implement price zone rectangle drawing.
- [ ] Implement text label drawing.
- [ ] Implement clear only agent-created drawings.
- [ ] Add MCP tools: `tv_draw_level`, `tv_draw_zone`, `tv_draw_label`, `tv_clear_agent_drawings`.
- [ ] Tag drawings with a stable prefix such as `marketData-agent`.

Suggested commits:

1. `Add chart annotation primitives`
2. `Add agent drawing cleanup`

Acceptance criteria:

- Agent drawings are distinguishable from user drawings.
- Cleanup does not remove unrelated user drawings.
- Manual verification confirms annotations appear on the visible chart.

## Phase 8: Analyze and Annotate Workflow

- [ ] Add a workflow adapter that combines history, analysis, chart control, drawing, and screenshot.
- [ ] Add MCP tool: `tv_analyze_and_annotate`.
- [ ] Support inputs: symbol, interval, lookback, analysis types, draw flag, screenshot flag.
- [ ] Return compact summary, levels, zones, chart actions, drawing counts, and screenshot path.
- [ ] Add fake-based tests for workflow orchestration.
- [ ] Add manual verification fixture and checklist.

Suggested commits:

1. `Add analyze and annotate workflow`
2. `Document chart analysis workflow`

Acceptance criteria:

- Tool can run in analysis-only mode without TradingView Desktop.
- Tool can run draw mode when Desktop CDP is available.
- User-visible annotations match the returned summary.

## Phase 9: Optional Advanced Features

- [ ] Read visible indicator values from the chart.
- [ ] Add indicator management with allowlisted indicator names.
- [ ] Add Pine Script editor support in a separate, opt-in module.
- [ ] Add Pine compile/check support only after documenting upstream calls.
- [ ] Add replay support only if it has a clear analysis workflow.
- [ ] Add multi-pane support only after single-chart flows are stable.

Suggested commits:

1. `Add indicator read tools`
2. `Add optional Pine Script tools`
3. `Add replay analysis helpers`

Acceptance criteria:

- Advanced tools remain opt-in.
- Tool output stays compact by default.
- Safety boundaries are updated before new control surfaces are exposed.

## Verification Checklist

Run after code changes unless the step is documentation-only:

```bash
.venv/bin/python -m unittest discover -s tests
```

For desktop automation phases, also verify manually:

- TradingView Desktop is running with `--remote-debugging-port=9222`.
- `tv_desktop_health` reports the expected chart target.
- Chart state tools return the visible symbol and timeframe.
- Drawing tools create visible annotations.
- Cleanup removes only agent-created drawings.

## Implementation Log

Use this section to record completed increments.

| Date | Commit or Branch | Change | Verification |
|---|---|---|---|
| 2026-04-19 | pending | Created feature plan | Documentation-only |
| 2026-04-19 | pending | Documented MCP roadmap and safety boundaries in README | Documentation-only |

## Current Next Step

Decide whether the MCP layer should call in-process Python services directly or call the local Flask API by default.
