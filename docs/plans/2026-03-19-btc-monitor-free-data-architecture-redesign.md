# BTC Monitor Free-Data Architecture Redesign

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the BTC long-term investment scoring system so that it remains economically meaningful, fully reproducible, and strictly limited to free public data sources.

**Architecture:** Replace the current flat multi-factor average with a three-layer architecture: long-term allocation regime, tactical execution timing, and budget execution control. Separate slow valuation and macro signals from short-term execution signals, and require minimum valid signal coverage before any buy decision is allowed.

**Tech Stack:** Python 3.12, pandas, requests, ccxt, yfinance, fredapi, pytest

---

## Non-Negotiable Constraint

This redesign must **not** use any paid API, paid dataset, commercial data terminal, premium scraping provider, or trial-only source.

Allowed source classes:
- Official public APIs with no payment required
- Free-tier APIs that remain usable without commercial subscription
- Public CSV/JSON/HTML endpoints with stable free access
- Historical free data that can be replayed in backtests

Disallowed source classes:
- Any source that requires billing setup
- Any source whose useful history is locked behind a paid tier
- Any source that forbids durable production use without commercial license
- Any signal whose live data is free but whose historical data is paid, if that signal is needed in backtests

This rule takes precedence over feature completeness. If a signal cannot be sourced for free, it must be downgraded to optional research status or removed.

## Problem Statement

The current system mixes slow valuation signals, short-term sentiment proxies, and partially implemented market structure signals into one weighted average. That creates four problems:

1. Economic meaning is diluted because long-horizon valuation and short-horizon execution inputs are treated as equivalent votes.
2. Some indicators are placeholders or weak proxies but still affect production decisions.
3. Missing-data normalization changes the meaning of the threshold from run to run.
4. The backtest does not represent the live 12-factor system, so thresholds are not calibrated against the real architecture.

For a long-term BTC allocation engine, the system should first answer: "Should capital be structurally added here?" Only after that should it answer: "Is this week a good time to execute?"

## Design Principles

- **Free-data only:** no paid dependencies, no exceptions.
- **Long-term first:** structural valuation decides whether buying is allowed.
- **Execution second:** tactical indicators only refine entry timing.
- **No placeholder alpha:** incomplete factors must not contribute positive score.
- **Minimum valid coverage:** buys require enough valid signal weight.
- **Backtest parity:** live logic and historical logic must share the same factor framework.
- **Interpretability over indicator count:** fewer independent signals are better than many correlated ones.

## Target Architecture

Split the strategy into three layers.

### 1. Strategic Layer

Purpose: determine the long-term BTC accumulation regime.

This layer uses only slow, high-meaning signals with multi-month relevance:
- `MVRV_Proxy`
- `Puell_Multiple`
- `Price_vs_200WMA`
- `Cycle_Drawdown`
- `Net_Liquidity`
- `10Y_Yield_Regime`

Output:
- `AGGRESSIVE_ACCUMULATE`
- `NORMAL_ACCUMULATE`
- `DEFENSIVE_HOLD`
- `RISK_REDUCE`

This layer is the gatekeeper. Tactical confirmation cannot override a structurally bearish regime into a buy.

### 2. Tactical Layer

Purpose: refine timing for execution once the strategic layer allows accumulation.

This layer uses shorter-horizon signals that help avoid poor near-term entries:
- Weekly RSI divergence
- Fear & Greed
- Short-term distance to 200WMA or recent drawdown snapback
- Optional free ETF proxy only if a stable free historical series is available

Output:
- `BUY_NOW`
- `STAGGER_BUY`
- `WAIT`

This layer must never be allowed to create structural conviction by itself.

### 3. Execution Layer

Purpose: translate regime plus timing into monthly budget actions.

Responsibilities:
- budget rollover
- max budget multiplier
- monthly buy cap
- split execution rules
- state persistence
- report generation

This layer produces the final action:
- `BUY`
- `PARTIAL_BUY`
- `WAIT`
- `ALERT`

## Factor Policy

Factors are grouped into three statuses.

### Core Factors

These are allowed in production and required for strategic decisions:
- `MVRV_Proxy`
- `Puell_Multiple`
- `200WMA`
- `Cycle_Position`
- `Net_Liquidity`
- `Yields`

### Secondary Factors

These may refine timing but cannot drive the core regime:
- `RSI_Div`
- `FearGreed`

### Research Factors

These are excluded from production score until they satisfy free-data, historical reproducibility, and reliability standards:
- `Production_Cost`
- `Options_Wall`
- `ETF_Flow`

Research factors may appear in the report as informational annotations, but must use `is_valid=False` and zero production weight.

## Free Data Source Policy

### Approved Sources

- BTC spot OHLCV:
  - Binance public market data
  - Yahoo Finance
  - CoinGecko
  - CryptoCompare
- Macro:
  - FRED
- On-chain:
  - Blockchain.com
  - Mempool.space
- Sentiment:
  - Alternative.me Fear & Greed

### Conditional Sources

A source may only be promoted into the approved set if all three are true:
- live endpoint is free
- historical replay is free
- parsing is stable enough for unattended use

### Rejected for Core Scoring

These should not be in core production scoring under the current free-data policy:
- Deribit options wall
- Tradier-dependent ETF options wall
- Any ETF flow signal based only on same-day page scraping
- Any proxy that lacks free historical backfill for backtests

## Scoring Model

Do not use a flat weighted average across all signals.

Use a staged model.

### Strategic Score

Compute a normalized strategic score from core factors only.

Suggested internal weights:
- Valuation block: 45%
  - `MVRV_Proxy`: 25%
  - `Puell_Multiple`: 20%
- Cycle block: 25%
  - `200WMA`: 15%
  - `Cycle_Position`: 10%
- Macro block: 30%
  - `Net_Liquidity`: 18%
  - `Yields`: 12%

Map the score to regime:
- `>= 70`: `AGGRESSIVE_ACCUMULATE`
- `50 to <70`: `NORMAL_ACCUMULATE`
- `30 to <50`: `DEFENSIVE_HOLD`
- `<30`: `RISK_REDUCE`

### Tactical Score

Compute a smaller execution score from secondary factors:
- `RSI_Div`: 40%
- `FearGreed`: 35%
- Short-term price stretch/reversion factor: 25%

Map the score to timing:
- `>= 65`: `BUY_NOW`
- `45 to <65`: `STAGGER_BUY`
- `<45`: `WAIT`

### Coverage Rules

Before any buy is permitted:
- strategic valid weight must be at least 70%
- all required core valuation signals must be present
- no research factor may substitute for a missing core factor

If coverage fails, default to `WAIT` and report `INSUFFICIENT_CORE_DATA`.

## Decision Rules

Decision logic should become rule-based instead of threshold-only.

- `AGGRESSIVE_ACCUMULATE + BUY_NOW` -> `BUY` with `1.5x` to `3.0x`
- `AGGRESSIVE_ACCUMULATE + STAGGER_BUY` -> `PARTIAL_BUY` with `1.0x` to `1.5x`
- `NORMAL_ACCUMULATE + BUY_NOW` -> `BUY` with `1.0x`
- `NORMAL_ACCUMULATE + STAGGER_BUY` -> `PARTIAL_BUY` with `0.5x`
- `NORMAL_ACCUMULATE + WAIT` -> `WAIT`
- `DEFENSIVE_HOLD` -> `WAIT`
- `RISK_REDUCE` -> `ALERT`

This keeps execution aligned with long-term conviction instead of letting one tactical oversold reading force a full buy.

## Module Restructure

Recommended code layout:

- `src/strategy/strategic_engine.py`
  - computes strategic score and regime
- `src/strategy/tactical_engine.py`
  - computes timing score and timing action
- `src/strategy/execution_engine.py`
  - combines regime, timing, and state into final action
- `src/strategy/policies.py`
  - source policy, valid-weight policy, required-factor lists
- `src/strategy/reporting.py`
  - renders report sections with explicit coverage and exclusions

Existing indicator modules can remain, but should be reclassified by layer.

## Changes to Existing Signals

### Keep

- `200WMA`
- `Puell_Multiple`
- `MVRV_Proxy`
- `Net_Liquidity`
- `Yields`
- `Cycle_Position`
- `RSI_Div`
- `FearGreed`

### Downgrade

- `Production_Cost`
  - remove from production score
  - keep only as future research placeholder

- `Options_Wall`
  - remove from production score
  - keep only if later supported by free live plus free historical data

- `ETF_Flow`
  - current implementation is not real flow data
  - replace with either a real free historical ETF proxy or remove entirely

## Reporting Requirements

The report should show:
- strategic regime
- tactical timing state
- final action
- valid core weight
- missing required factors
- excluded research factors
- budget multiplier

This avoids the false impression that every printed line contributed equally to the decision.

## Backtest Redesign

The backtest must mirror the live architecture.

Rules:
- use the same strategic factor set as production
- use only free historical sources
- mark unavailable factors invalid rather than silently replacing them
- backtest regime and timing separately, then combine them
- simulate monthly budget rollover, not just long/flat exposure

Outputs should include:
- action history by month
- budget multiplier utilization
- average buy price vs benchmark DCA
- cash deployment efficiency
- regime distribution over time

The current long/flat backtest is useful as a market-timing experiment, but it is not a valid proxy for a monthly BTC accumulation engine.

## Testing Strategy

Add tests in five groups.

1. Source policy tests
- verify forbidden sources never enter core scoring
- verify research factors are excluded from production weights

2. Strategic engine tests
- verify regime mapping from core scores
- verify minimum valid weight behavior
- verify required-core-signal gating

3. Tactical engine tests
- verify timing mapping
- verify tactical signals cannot trigger buy under bearish regime

4. Execution engine tests
- verify budget multiplier outcomes
- verify monthly buy cap
- verify partial buy behavior

5. Backtest parity tests
- verify live and historical scoring use the same factor registry
- verify invalid-factor handling is identical

## Migration Plan

### Phase 1: Safety Cleanup

- mark `Production_Cost` as invalid research-only
- remove `Options_Wall` and `ETF_Flow` from live production weighting
- add report labels for `core`, `secondary`, and `research`

### Phase 2: Strategy Split

- introduce strategic and tactical engines
- move current aggregation logic out of `StrategyEngine`
- implement coverage gating and required-core rules

### Phase 3: Execution Upgrade

- replace single buy threshold logic with regime plus timing rules
- add `PARTIAL_BUY`
- preserve current monthly rollover semantics where still appropriate

### Phase 4: Backtest Parity

- redesign the backtest around monthly execution
- calibrate new regime thresholds from free historical data

### Phase 5: Optional Research Re-entry

- only reintroduce a research factor if it gains free live and free historical support
- require dedicated tests and separate ablation analysis before promotion

## Implementation Tasks

### Task 1: Freeze paid and unstable sources out of production

**Files:**
- Modify: `src/strategy/engine.py`
- Modify: `src/indicators/valuation.py`
- Modify: `src/indicators/options_etf.py`
- Test: `tests/unit/test_strategy_engine.py`
- Test: `tests/unit/test_options_etf.py`

**Step 1:** Write failing tests that assert research factors do not contribute to production score.

**Step 2:** Mark `Production_Cost`, `Options_Wall`, and current `ETF_Flow` as research-only or invalid in production.

**Step 3:** Run targeted tests and update report output.

### Task 2: Introduce strategy layering

**Files:**
- Create: `src/strategy/strategic_engine.py`
- Create: `src/strategy/tactical_engine.py`
- Create: `src/strategy/policies.py`
- Modify: `src/strategy/engine.py`
- Test: `tests/unit/test_strategy_engine.py`

**Step 1:** Write failing tests for regime and timing separation.

**Step 2:** Implement strategic score calculation from core factors only.

**Step 3:** Implement tactical score calculation from secondary factors only.

**Step 4:** Update orchestration entrypoint to combine both layers.

### Task 3: Upgrade execution logic

**Files:**
- Create: `src/strategy/execution_engine.py`
- Modify: `src/state/tracker.py`
- Modify: `src/strategy/engine.py`
- Test: `tests/unit/test_state_tracker.py`
- Test: `tests/unit/test_strategy_engine.py`

**Step 1:** Write failing tests for `BUY`, `PARTIAL_BUY`, `WAIT`, and `ALERT`.

**Step 2:** Implement regime-driven budget logic.

**Step 3:** Keep month rollover deterministic and explicitly timezone-aware.

### Task 4: Redesign reporting

**Files:**
- Create: `src/strategy/reporting.py`
- Modify: `src/strategy/engine.py`

**Step 1:** Render layer-by-layer report sections.

**Step 2:** Show coverage failures and excluded research factors.

### Task 5: Rebuild backtest for parity

**Files:**
- Modify: `src/backtest/btc_backtest.py`
- Create: `tests/unit/test_backtest_parity.py`

**Step 1:** Write failing tests asserting factor registry parity with live strategy.

**Step 2:** Simulate monthly budget deployment rather than simple long/flat exposure.

**Step 3:** Calibrate strategic and tactical thresholds only from free historical data.

## Success Criteria

The redesign is complete when:
- no paid source is used anywhere in production decision-making
- placeholder factors contribute zero production score
- strategic and tactical decisions are separated
- buy actions require minimum valid core coverage
- live and backtest logic use the same factor framework
- reports clearly distinguish core, secondary, and research signals

## Out of Scope

- automated order execution
- leverage or derivatives trading
- paid on-chain datasets
- premium ETF flow feeds
- intraday market-making or short-term trading features

