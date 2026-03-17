## GEMINI.md - BTC Monitor Context

## Project Overview
**BTC Monitor** is a quantitative decision-support system designed for long-term Bitcoin investors. It evaluates market conditions once a week (Monday 21:00 Paris Time) using a multi-factor resonance model to determine optimal Dollar-Cost Averaging (DCA) timing and provide portfolio rebalancing alerts.

### Core Architecture
- **Language**: Python 3.12
- **Data Fetchers**: `ccxt` (Binance), `fredapi` (Macro data), `yfinance` (ETF/BITO data).
- **Strategy Engine**: Orchestrates evaluation, scoring, and decision making.
    - **Scoring**: Individual indicators return an `IndicatorResult` with a score from `-10` to `10`. The engine aggregates these using a weighted average and scales the result to a `-100` to `100` range.
    - **Normalization**: If an API fails, the system automatically excludes that indicator's weight from the calculation, ensuring the final score remains valid and representative of the available data.
- **State Management**: Manages `data/state.json` via `StateTracker`.
    - **Budget Rollover**: If no buy signal occurs in a month, the budget multiplier increases by `1.0x` (capped at `MAX_BUDGET_MULTIPLIER`, default `3.0x`).
    - **Reset**: The multiplier resets to `1.0x` after a `BUY` action is executed.

## Building and Running

### Environment Setup
1.  **Dependencies**: Managed via `requirements.txt` (includes `pandas`, `ccxt`, `fredapi`, `pytest`).
2.  **Configuration**: Uses `.env` for API keys and thresholds (`THRESHOLD_BUY`, `THRESHOLD_SELL`).
3.  **Docker**: Primary environment using `python:3.12-slim`.

### Key Commands

#### Development & Testing
- **Run Immediate Evaluation (Dry-run)**:
  ```bash
  docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt && PYTHONPATH=. python src/main.py --now"
  ```
- **Run All Tests**:
  ```bash
  docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt && PYTHONPATH=. pytest tests"
  ```

#### Production
- **Build and Start Service**:
  ```bash
  docker-compose up -d --build
  ```

## Development Conventions

### 1. Indicator Design
- All indicators must return an `IndicatorResult` object:
  - `name`: Identifier for the indicator.
  - `score`: Normalized value from `-10.0` to `10.0`.
  - `is_valid`: Set to `False` if data fetching or calculation fails.
  - `weight`: Defaults to `1.0`, used for weighted scoring.

### 2. State Persistence
- All persistent data is stored in `data/state.json`.
- Key state fields: `current_month`, `has_bought_this_month`, `accumulated_budget_multiplier`, `history`.

### 3. Testing
- **Unit Tests**: Focus on individual logic using `pytest-mock` (e.g., `mocker.patch.object(fetcher, 'get_series', ...)`).
- **E2E Tests**: Verify the full `run_strategy_cycle` logic.

### 4. Configuration
- Use `src/config.py` as the single source of truth for settings.
- Default buy threshold is `60.0`, and sell threshold is `-40.0`.
