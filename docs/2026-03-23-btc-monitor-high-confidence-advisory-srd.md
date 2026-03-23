# BTC Monitor SRD: High-Confidence BTC Position Advisory Refactor

> **For Claude Code:** This document is the source of truth for reviewing and refactoring `btc-monitor` from a budgeted DCA executor into a high-confidence BTC add/reduce advisory engine. The core decision path must fail closed when required evidence is missing. Budget, capital sizing, and monthly rollover logic are out of scope for the target system.

## Metadata

- Status: Review complete, refactor not started
- Date: 2026-03-23
- Audience: Maintainers and Claude Code agents
- Scope: Current-system evaluation, factor completeness audit, backtest credibility audit, refactor requirements, and acceptance criteria

## Acceptance Decision

The current system is **not accepted** for the target use case of high-confidence BTC add/reduce advice.

It is acceptable as a conservative regime monitor and DCA helper, but it does not yet meet the standard for high-confidence position guidance because:

- coverage rules are reported but not enforced in the decision path
- advisory logic is mixed with budget and execution state
- the strategic factor set is too correlated and not broad enough
- the tactical layer is too weak for confident reduce calls
- the backtest measures portfolio return, not advisory quality
- committed backtest artifacts are inconsistent with current code output

## Objective

Build a decision-support engine that produces **advice only**, not execution:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

Each recommendation must include:

- confidence score
- factor evidence summary
- missing-data blockers
- conflict flags
- source freshness

## Non-Goals

- no budget multiplier
- no accumulated monthly cash logic
- no stateful position sizing
- no auto-execution
- no paid APIs or paid datasets
- no claim of exact market top or bottom timing

## Verification Performed

The following verification was completed on 2026-03-23:

- reviewed `src/`, `tests/unit/`, `README.md`, `GEMINI.md`, and `docs/plans/`
- ran `docker compose run --rm tests`
- result: 39 unit tests passed
- reran the current backtest in Docker from the current code path
- observed rerun metrics: total return `11.55`, CAGR `17.44%`, max drawdown `-35.74%`, exposure `16.26%`, trades `6`
- verified that the current backtest output schema does not match the committed `data/backtest` CSV
- executed a logic probe showing that one valid strategic factor plus strong tactical inputs can still produce `BUY`

## Current System Strengths

The current repository has several sound building blocks:

- layered separation exists between strategic, tactical, and execution logic
- research-only factors are excluded from production scoring
- the report surfaces coverage, missing core factors, and excluded research factors
- unit-test coverage is good for a small project
- backtest timing is mostly sane: signals are computed on the current weekly close and trades use the next weekly open

These strengths are useful, but they do not offset the issues below.

## Critical Findings

### 1. Coverage gating is not enforced in the decision path

`MIN_STRATEGIC_VALID_RATIO` exists in `src/strategy/policies.py`, but it is only used in `src/strategy/reporting.py`.

`StrategyEngine.calculate_final_score()` in `src/strategy/engine.py` only checks whether **any** non-research strategic result is valid. It does not require:

- minimum strategic coverage
- required core-factor presence
- separate coverage checks for `ADD` and `REDUCE`

Proof from local verification:

- a synthetic run with only `MVRV_Proxy` valid and both tactical factors positive still produced `BUY`
- observed result: `strategic_score=100`, `tactical_score=100`, `action=BUY`

This is disqualifying for a high-confidence advisory engine.

### 2. The current product is still an execution engine, not an advisory engine

The current control flow is built around `ExecutionEngine`, `StateTracker`, `monthly_action_count`, and `accumulated_budget_multiplier`.

This is appropriate for staged DCA execution, but it is not appropriate for pure advice because it couples:

- signal quality
- capital deployment rules
- monthly pacing constraints

High-confidence advice should be stateless at the core decision layer.

### 3. The strategic factor set is too correlated

The nominal strategic layer contains six factors:

- `MVRV_Proxy`
- `Puell_Multiple`
- `200WMA`
- `Cycle_Pos`
- `Net_Liquidity`
- `Yields`

In practice, this is closer to three independent evidence blocks:

- price-location proxies: `MVRV_Proxy`, `200WMA`, `Cycle_Pos`
- miner stress: `Puell_Multiple`
- macro liquidity: `Net_Liquidity`, `Yields`

This means the system appears more diversified than it really is.

### 4. The tactical layer is too weak for high-confidence reduce decisions

The tactical layer currently relies on:

- `RSI_Div`
- `FearGreed`

That is too thin for confident add/reduce advice. It gives weak evidence for:

- sustained overheating
- risk-off microstructure deterioration
- tactical re-entry after local washouts

### 5. Architecture drift remains in the live path

The code still computes factors that do not affect production decisions:

- `Pi_Cycle` is still evaluated in `src/strategy/engine.py`
- `Pi_Cycle` is treated as excluded in reporting because it is not in `src/strategy/policies.py`

The configuration surface also drifts from behavior:

- `THRESHOLD_BUY` and `THRESHOLD_SELL` still exist in `src/config.py`
- these thresholds are no longer used by the layered execution path
- docs still describe threshold-based behavior and full live/backtest alignment more strongly than the code supports

### 6. Research factors are correctly excluded, but no production-grade replacement exists

`Production_Cost`, `Options_Wall`, and `ETF_Flow` are correctly marked research-only.

The problem is not that they are excluded. The problem is that the system does not replace them with a reliable, historically replayable microstructure block.

That leaves the engine underpowered exactly where high-confidence add/reduce advice needs more evidence.

## Factor Completeness Audit

### Current factors that should remain

- `Puell_Multiple`
  - independent and economically meaningful
- `200WMA`
  - useful as a slow trend anchor
- `Net_Liquidity`
  - important macro liquidity proxy
- `Yields`
  - useful macro tightening proxy if redefined as regime rather than one-week delta
- `FearGreed`
  - acceptable as a tactical sentiment input
- `RSI_Div`
  - acceptable as a tactical confirmation input

### Current factors that should remain but be downgraded in confidence

- `MVRV_Proxy`
  - useful, but it is still a proxy based on a 730-day moving average rather than true realized-cap data
- `Cycle_Pos`
  - useful as supporting context, but it is too correlated with price-location factors to carry full strategic weight by itself

### Factors that should be removed from the live production path or formalized as research-only

- `Pi_Cycle`
  - currently computed but excluded
  - either remove it from live evaluation or explicitly define it as research-only
- `Production_Cost`
  - keep research-only until a durable free-data model exists
- `Options_Wall`
  - keep research-only until both live and historical data are stable and replayable
- `ETF_Flow`
  - keep research-only until a free historical source is formalized

### Missing factors needed for high-confidence add/reduce advice

The target engine needs at least one additional factor in each of the blocks below.

### A. Stronger independent bottom/recovery factor

Recommended addition:

- `Hash_Ribbon` or equivalent miner-stress recovery signal using free hash-rate and difficulty data

Reason:

- this adds a bottom/recovery lens that is not just another price-location proxy

### B. Broader macro risk block

Recommended addition:

- `DXY_Regime` from FRED
- or `10Y_Real_Yield_Regime` if a robust free source is available

Reason:

- `Net_Liquidity` and nominal 10Y yield are not enough for high-confidence macro filtering

### C. Tactical stretch factor

Recommended addition:

- short-term stretch or reversion percentile
- example: 4-week price stretch versus 200DMA or 26-week trend anchor

Reason:

- this makes `STAGGER_BUY` or intermediate tactical states reachable without over-relying on RSI divergence

### D. A formal risk-off confirmation block for reduce calls

Recommended addition:

- one free and replayable market-structure factor, such as basis/funding/open-interest regime, only if it satisfies free-history and stability requirements

Reason:

- reduce calls should not be triggered by one overheated price-location factor alone

### Factor policy for the target system

The target system should enforce block-level independence:

- `ADD` requires bullish evidence from at least three independent blocks
- `REDUCE` requires bearish evidence from at least two independent blocks, with at least one non-price-location block
- missing required blocks must return `INSUFFICIENT_DATA`

## Backtest Credibility Audit

### What is credible today

- signal timing mostly avoids same-bar execution bias
- live/backtest parity tests exist and pass
- research-only factors are invalidated in backtest instead of being silently guessed

### What is not credible enough for the target use case

### 1. Backtest semantics change when data is missing

Macro history depends on `FRED_API_KEY`.

If macro data is unavailable:

- `Net_Liquidity` and `Yields` become invalid
- the strategy still runs
- the meaning of the strategic score changes

For a high-confidence system, missing required macro blocks must fail closed.

### 2. The tactical layer degrades in backtest

Current backtest facts from a local rerun of the current code:

- tactical score took only three values: `-100`, `0`, `100`
- `STAGGER_BUY` never occurred
- action distribution was heavily skewed:
  - `ALERT`: 538
  - `WAIT`: 252
  - `BUY`: 15
  - `WAIT (Already Acted)`: 13

This shows that the tactical layer is not being exercised as a rich timing model in historical replay.

### 3. The backtest optimizes the wrong thing for the target product

Current backtest output is portfolio-return oriented:

- total return
- CAGR
- volatility
- Sharpe
- drawdown
- trade count

That is appropriate for an execution strategy, but the target product is an advisory engine.

It also produces a portfolio profile that is clearly not aligned with long-term BTC participation:

- rerun exposure was only `16.26%`
- rerun total return was `11.55`
- buy-and-hold return in the same run was several orders of magnitude larger

This means the current backtest is validating a sparse long/flat filter, not a high-confidence add/reduce advisory framework.

The target backtest must measure:

- forward 4-week, 12-week, and 26-week returns after each recommendation
- precision of `ADD`
- precision of `REDUCE`
- false-positive and false-negative rates
- regime lag around cycle turns
- monotonicity of confidence buckets

### 4. The committed backtest artifacts are stale

The committed `data/backtest/btc_backtest_weekly.csv` does not match the current code schema.

Current code writes:

- `strategic_score`
- `tactical_score`
- `action`

The committed CSV in the repository does not contain those columns.

The committed metrics file also differs materially from a local rerun of the current code:

- committed metrics: total return `25295.27`, CAGR `90.65%`, exposure `50.43%`, trades `4`
- current-code rerun: total return `11.55`, CAGR `17.44%`, exposure `16.26%`, trades `6`

This makes the checked-in artifacts unsuitable as acceptance evidence.

### 5. Full-history single-run evaluation is not enough

Bitcoin has multiple structurally different regimes. A single full-history run hides whether the strategy only works because of one favorable segment.

The target validation should include:

- cycle-sliced evaluation
- walk-forward windows
- regime-conditioned performance tables

## Target Product Requirements

### Product behavior

The target engine must emit:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

The output payload must include:

- confidence score from 0 to 100
- strategic state
- tactical state
- ordered supporting factors
- ordered conflicting factors
- missing required factors
- source timestamps
- explanation text for humans

### Decision rules

The target engine must not map score directly to action.

It must use rule-based gating:

- `ADD` requires minimum coverage and agreement across independent evidence blocks
- `REDUCE` requires explicit overheating or deterioration agreement across independent blocks
- conflicting evidence lowers confidence
- missing required data returns `INSUFFICIENT_DATA`

### Architecture requirements

Recommended module split:

- `src/strategy/factor_registry.py`
  - source of truth for factor metadata
- `src/strategy/strategic_engine.py`
  - slow regime inference only
- `src/strategy/tactical_engine.py`
  - short-horizon confirmation only
- `src/strategy/advisory_engine.py`
  - final advice and confidence
- `src/strategy/reporting.py`
  - advice report only
- `src/backtest/advisory_backtest.py`
  - advisory-quality validation only

The core advisory path must not depend on:

- `StateTracker`
- `MAX_BUDGET_MULTIPLIER`
- `monthly_action_count`
- `accumulated_budget_multiplier`

### Reporting requirements

The report must make blocked decisions explicit:

- `coverage failed`
- `required macro block missing`
- `reduce signal blocked by missing confirmation`
- `research factor excluded`

The report must not imply that a recommendation is actionable if the engine is missing required evidence.

## Recommended Refactor Sequence

1. Remove budget and monthly state from the core decision path.
2. Add block-level coverage enforcement to the advisory engine.
3. Formalize factor metadata and independence groups in a registry.
4. Remove or reclassify `Pi_Cycle`.
5. Add one stronger non-price recovery factor and one broader macro factor.
6. Replace portfolio-return backtest as the main acceptance artifact with advisory-quality validation.
7. Regenerate and recommit backtest artifacts only after the new schema is stable.
8. Align `README.md`, `GEMINI.md`, and `src/config.py` with actual runtime behavior.

## Acceptance Criteria

The refactor is accepted only when all of the following are true:

- the core engine emits `ADD`, `REDUCE`, `HOLD`, or `INSUFFICIENT_DATA`
- the core engine no longer depends on budget or monthly execution state
- `ADD` and `REDUCE` both fail closed when required factor blocks are missing
- a one-factor bullish scenario cannot produce `ADD`
- a one-factor overheated scenario cannot produce `REDUCE`
- `Pi_Cycle` is either removed from live evaluation or explicitly marked research-only
- backtest and live output schemas match
- committed backtest artifacts are regenerated from the current code and include the current schema
- advisory backtest reports forward-return precision for each recommendation bucket
- cycle-sliced or walk-forward validation is documented
- README and repo docs no longer claim coverage enforcement unless it is implemented in code
- Docker test suite passes

## Current Status Against Acceptance Criteria

Current status: **Rejected**

Reasons:

- advice is still coupled to execution state
- coverage gating is not enforced in the decision path
- required factor blocks are not enforced
- backtest is not measuring advisory quality
- committed acceptance artifacts are stale

## Deliverable of This Review

This SRD is the acceptance report for the current system and the source document for the next refactor.

It does not approve the current implementation for high-confidence add/reduce advice.
