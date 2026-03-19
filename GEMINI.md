## GEMINI.md - BTC Monitor Context

## Project Overview
**BTC Monitor** is a quantitative decision-support system designed for long-term Bitcoin investors. It evaluates market conditions on demand via an external scheduler using a layered model to determine long-term accumulation regime, tactical timing, and monthly budget execution.

### Core Architecture
- **Language**: Python 3.12
- **Data Policy**: Production logic must not depend on paid APIs or paid market data.
- **Data Fetchers**: 
    - `ccxt` (Binance): Technical & Price data.
    - `fredapi` (Macro data): Fed liquidity & Treasury yields.
    - `yfinance` (ETF/BITO data): Research-only ETF and options proxies.
    - `Blockchain.info` & `Mempool.space`: Public on-chain fundamental data (MVRV, Puell Multiple, Hashrate).
- **Strategy Engine**: Orchestrates evaluation, scoring, and decision making.
    - **Scoring**: Indicators still emit `IndicatorResult`, but production decisions are layered into strategic, tactical, and execution stages rather than one flat weighted vote.
    - **Strategic Layer**: `200WMA`, `Cycle_Pos`, `Net_Liquidity`, `Yields`, `MVRV_Proxy`, `Puell_Multiple`.
    - **Tactical Layer**: `RSI_Div`, `FearGreed`.
    - **Research-only Factors**: `Production_Cost`, `Options_Wall`, and `ETF_Flow` remain visible in reports but are excluded from production scoring.
    - **Normalization**: Missing data reduces coverage; core-factor and minimum-coverage rules are enforced before a buy can be promoted.
- **State Management**: Manages `data/state.json` via `StateTracker`.
    - **Budget Rollover**: If no buy signal occurs in a month, the budget multiplier increases by `1.0x` (capped at `MAX_BUDGET_MULTIPLIER`, default `3.0x`).
    - **Execution Tracking**: State also records `monthly_action_count`, timing/regime metadata, and timezone-aware action timestamps.
    - **Reset**: The multiplier resets after a full `BUY`; partial execution keeps the remaining monthly budget semantics intact.

## Building and Running

### Environment Setup
1.  **Dependencies**: Managed via `requirements.txt` (includes `pandas`, `ccxt`, `fredapi`, `pytest`).
2.  **Configuration**: Uses `.env` for API keys and thresholds (`THRESHOLD_BUY`, `THRESHOLD_SELL`).
3.  **Docker**: Primary environment is the project image built from `Dockerfile`.

### Key Commands

#### Development & Testing
- **Run Immediate Evaluation (Dry-run)**:
  ```bash
  docker compose build
  docker compose run --rm app
  ```
- **Run All Tests**:
  ```bash
  docker compose run --rm tests
  ```

#### Production
- **Build and Start Service**:
  ```bash
  docker compose build
  docker compose run --rm app
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
- Key state fields: `current_month`, `has_bought_this_month`, `accumulated_budget_multiplier`, `monthly_action_count`, `last_action_date`, `history`.

### 3. Testing
- **Unit Tests**: Focus on individual logic using `pytest-mock` (e.g., `mocker.patch.object(fetcher, 'get_series', ...)`).
- **Parity Coverage**: Keep live strategy composition and backtest composition aligned with parity tests.

### 4. Configuration
- Use `src/config.py` as the single source of truth for settings.
- Default buy threshold is `60.0`, and sell threshold is `-40.0`.
