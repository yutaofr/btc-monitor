# Repository Guidelines

## Project Structure & Module Organization
The core application lives in `src/` and is organized by responsibility:
- `src/main.py` is the entry point and scheduler.
- `src/config.py` loads environment variables and thresholds.
- `src/indicators/` contains market signal calculations (technical, macro, sentiment, options/ETF).
- `src/fetchers/` wraps external data sources (Binance, FRED).
- `src/strategy/` scores signals and makes buy/hold decisions.
- `src/state/` persists run state.
Tests live in `tests/unit/`. `tests/e2e/` is reserved for integration coverage. Runtime data (state, logs) is stored under `data/`.

## Build, Test, and Development Commands
The repo is Docker-first; these are the canonical commands:
```bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim \
  bash -c "pip install -r requirements.txt && PYTHONPATH=. python src/main.py --now"

docker run --rm -v $(pwd):/app -w /app python:3.12-slim \
  bash -c "pip install -r requirements.txt && PYTHONPATH=. pytest tests/unit"

docker-compose up -d app
```
For local development without Docker, use Python 3.12 and `pip install -r requirements.txt`, then run `PYTHONPATH=. python src/main.py --now`.

## Coding Style & Naming Conventions
Follow standard Python conventions (PEP 8):
- 4-space indentation, no tabs.
- `snake_case` for functions/variables, `CapWords` for classes.
- Module and package names are lowercase with underscores.
No formatter or linter is enforced, so keep changes small and consistent with nearby code.

## Testing Guidelines
Tests are written with `pytest` (see `requirements.txt`). Name tests `test_*.py` and keep them in `tests/unit/`, mirroring the module under test. Run all unit tests with `pytest tests/unit`. Add tests for new indicators, fetchers, or strategy changes.

## Commit & Pull Request Guidelines
Existing history uses short, imperative commit summaries (for example, `add README`, `init project`). Keep the first line concise and descriptive. PRs should include:
- A summary of what changed and why.
- Linked issues or context if applicable.
- Test results (command + outcome).
Screenshots are not required unless output formatting changes.

## Configuration & Security
Copy `.env.example` to `.env` and set API keys (FRED, optional Telegram). Never commit secrets or `.env`. Prefer running via Docker to keep dependencies isolated.
