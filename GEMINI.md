## GEMINI.md - BTC Monitor Context

**BTC Monitor** is a quantitative decision-support system designed for long-term Bitcoin investors. It evaluates market conditions on demand via an external scheduler using a **stateless advisory architecture** to determine high-confidence accumulation regimes and output purely directional advice (`ADD`, `REDUCE`, `HOLD`), rather than handling direct wallet execution logic.

### Core Architecture
- **Language**: Python 3.12
- **Data Policy**: Production logic must not depend on paid APIs or paid market data.
- **Data Fetchers**: 
    - `ccxt` (Binance): Technical & Price data.
    - `fredapi` (Macro data): Fed liquidity, US Treasury Yields, DXY.
    - `yfinance` (ETF/BITO data): Research-only ETF and options proxies.
    - `Blockchain.info` & `Mempool.space`: Public on-chain fundamental data (MVRV, Puell Multiple, Hashrate).
- **Advisory Engine**: Dual-branch stateless orchestration via `FactorRegistry`.
    - **Position Branch** (`PositionAdvisoryEngine`): Outputs `ADD`, `REDUCE`, or `HOLD` for existing portfolio management. Requires comprehensive strategic alignment and tactical confirmation.
    - **Incremental Cash Branch** (`IncrementalBuyEngine`): Outputs `BUY_NOW`, `STAGGER_BUY`, or `WAIT` for new capital deployment. Evaluated against a time-weighted DCA benchmark.
    - **Strategic Engine**: Evaluates `liquidity`, `valuation`, and `trend` evidence blocks.
    - **Tactical Engine**: Confirms setup momentum via `RSI_Div`, `FearGreed`, and `Short_Term_Stretch`.
    - **Research-only Factors**: Flags like `ETF_Flow` remain visible in reports but strictly isolated from advisory gates or confidence.
    - **Fail-Closed & Hard Gating**: Missing necessary block evidence (e.g., missing Macro or Valuation data) systematically blocks aggressive actions (`ADD`, `BUY_NOW`, `REDUCE`), downgrading them to `HOLD`/`WAIT`/`STAGGER_BUY` via explicit `missing_required_factors` validation.
- **Factor Registry**: The single source of truth for all indicator metadata (`src/strategy/factor_registry.py`), defining cross-branch gating requirements (`is_required_for_buy_now`, `is_wait_veto`, etc.).
- **Reports**: Explicit markdowns built in `src/strategy/reporting.py` consuming dual-branch recommendation semantics.

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

### 2. State Mapping & Logic Flow
- Engine processes strictly independent pieces of evidence via the registry.
- Legacy execution state files (like `state.json`) are heavily decoupled or replaced. Adhere strictly to the `FactorDefinition` definitions.

### 3. Testing
- **Unit Tests**: Focus on individual logic using `pytest` fixtures and dependency injection. Mocks explicitly intercept `evaluate_history` during backtesting runs.
- **Parity Coverage**: Keep live strategy composition and backtest composition precisely mirrored. Backtests dump exact metric evaluations (`28_day_return`, `precision`).

### 4. Configuration
- Use `src/config.py` as the single source of truth for settings.
- Default buy threshold is `60.0`, and sell threshold is `-40.0`.
