# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `tradingview_service/`. Keep HTTP wiring in `app.py`, auth and websocket behavior in `auth.py` and `client.py`, configuration in `config.py`, and shared data logic in `models.py` and `cache.py`. The entrypoint is `run.py`. Tests live in `tests/` and mirror the module split with files such as `test_app.py` and `test_client.py`.

## Build, Test, and Development Commands
Create a local environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the service locally with:

```bash
.venv/bin/python run.py
```

The app listens on port `6969` by default. Run the full test suite with:

```bash
.venv/bin/python -m unittest discover -s tests
```

## Coding Style & Naming Conventions
Use Python with 4-space indentation and follow PEP 8 naming. Prefer `snake_case` for functions, variables, and modules, and `PascalCase` for classes like `TradingViewAuthenticator`. Keep functions focused and place small, reusable helpers near the behavior they support. No formatter or linter is configured here, so keep edits consistent with the surrounding code.

## Testing Guidelines
This project uses the standard library `unittest` framework. Add tests alongside the module you change and name files `test_<module>.py`. Favor deterministic unit tests with fakes or mocks over live network calls. Cover both success and error paths for API handlers, auth behavior, and websocket parsing.

## Commit & Pull Request Guidelines
There is no local Git history in this workspace, so use clear imperative commit messages, for example: `Add anonymous runtime guard`. Keep each commit scoped to one change. Pull requests should include a short summary, test evidence, any config changes, and sample requests or responses when API behavior changes.

## Security & Configuration Tips
Do not commit `.env` or any real TradingView credentials. The service now runs anonymously by default; only set `TRADINGVIEW_USE_CREDENTIALS=1` when credentialed mode is intentionally required.
