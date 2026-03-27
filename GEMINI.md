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
- **Advisory Engine**: Integrated orchestration via `FactorRegistry`.
    - **V3.0 TADR (Primary Path)**: Integrated `TADREngine` providing continuous `Target Allocation %` (20%-80%), probabilistic confidence scoring, and dynamic weighting based on Correlation Context.
    - **V2.0 Legacy (Support)**: Discrete engines (`PositionAdvisoryEngine`, `IncrementalBuyEngine`) for backward compatibility in reporting.
    - **Strategic Engine**: Evaluates `liquidity`, `valuation`, and `trend` evidence blocks.
    - **Tactical Engine**: Confirms setup momentum via `RSI_Div`, `FearGreed`, and `Short_Term_Stretch`.
    - **Research-only Factors**: Flags like `ETF_Flow` remain visible in reports but strictly isolated from advisory gates or confidence.
    - **Fail-Closed & Circuit Breaker**: `ProbabilisticConfidenceScorer` with a 2-critical-factor failure threshold forcing confidence to 0.0 and triggering a SYSTEM_GATE_LOCKED state.
- **Numerical Integrity**: Mandatory use of `quantize_score` (8-digit precision) for all intermediate terms and final sums to ensure **Bit-identical Parity** between live and backtest environments.
- **Factor Registry**: The single source of truth for all indicator metadata (`src/strategy/factor_registry.py`), defining cross-branch gating and V3 weights.
- **Strategy Monitoring**: 
    - **Rolling Correlation**: Detects shifts in BTC's correlation with macro factors (DXY, Yields).
    - **Sliding Window Analysis**: Compares Last 12 Months (LTM) precision vs. full history to detect "strategy drift".
    - **Drift Warning**: Automatically flags performance degradation in reports if LTM precision drops >15% (3*SE threshold).
- **Reports**: Explicit markdowns built in `src/strategy/reporting.py` consuming V3.0 `TADRInternalState`.

## Building and Running

### Environment Setup
1.  **Dependencies**: Managed via `requirements.txt` (includes `pandas`, `ccxt`, `fredapi`, `pytest`).
2.  **Configuration**: Uses `.env` for API keys and thresholds (`THRESHOLD_BUY`, `THRESHOLD_SELL`).
3.  **Docker**: Primary environment is the project image built from `Dockerfile`.

### Key Commands

#### Development & Testing
- **Run Immediate Evaluation (Snapshot)**:
  ```bash
  docker compose build
  docker compose run --rm app
  ```
- **Run V3.0 Acceptance Audit**:
  ```bash
  export PYTHONPATH=$PYTHONPATH:. && python3 tests/acceptance/verify_tadr_v3.py
  ```
- **Run All Tests (Unit + Parity)**:
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
