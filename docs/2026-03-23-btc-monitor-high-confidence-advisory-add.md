# BTC Monitor ADD: Calibrated Advisory Decision Architecture

> **For Claude Code:** This ADD defines the target architecture that implements the SRD in `docs/2026-03-23-btc-monitor-high-confidence-advisory-srd.md`. Treat this document as the design source of truth for the advisory refactor. The live path is already stateless; the remaining design problem is confidence calibration, horizon-aware validation, and stronger precision for `ADD` / `REDUCE`. Do not reintroduce budget pacing, position sizing, or execution state into the core decision path.

## Metadata

- Status: Proposed, refinement of the now-stateless advisory path
- Date: 2026-03-23
- Type: Architecture design and decision document
- Parent: `docs/2026-03-23-btc-monitor-high-confidence-advisory-srd.md`

## Executive Decision

`btc-monitor` will be refined into a **calibrated advisory engine** that emits high-confidence BTC position guidance only:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

The new design rejects flat score-to-action mapping as the primary control mechanism. It replaces it with:

- explicit factor metadata
- independent evidence blocks
- fail-closed coverage gates
- rule-based action eligibility
- confidence derived from evidence quality, agreement, conflict, and historical calibration
- multi-horizon validation, not one-horizon optimism

## Goals

- produce advice only, not execution
- separate strategy evaluation from capital management
- require independent evidence before `ADD` or `REDUCE`
- make missing-data behavior explicit and conservative
- keep all production inputs free, replayable, and testable
- validate the system on advisory quality rather than portfolio PnL alone
- calibrate confidence against historical precision and horizon performance

## Non-Goals

- no budget multiplier
- no monthly rollover
- no persistent execution state in the core path
- no auto-trading
- no paid data sources
- no exact price target or exact top/bottom forecast

## Architecture Principles

### 1. Advice is stateless

The core engine must answer one question: what is the best recommendation given current evidence?

It must not answer:

- how much capital to deploy
- whether the system already acted this month
- how much unused budget remains

### 2. Evidence blocks must be independent

The engine must avoid overcounting multiple variants of the same idea. Price-location factors are one block, not three independent votes.

### 3. `ADD` and `REDUCE` require different proof standards

`ADD` and `REDUCE` are not symmetric inverses.

- `ADD` needs strong valuation or recovery evidence, plus trend and macro confirmation
- `REDUCE` needs overheating or deterioration evidence, plus at least one non-price confirmation block

### 4. Missing required evidence must fail closed

If required blocks are absent, the engine returns `INSUFFICIENT_DATA`, not a weaker form of `ADD` or `REDUCE`.

### 5. Confidence is a product output

Confidence is not a cosmetic number. It must be derived from:

- coverage quality
- factor freshness
- block agreement
- block conflict
- factor confidence class
- historical precision by confidence bucket
- horizon-specific correctness

## Target System Overview

The new system has five logical layers:

1. Data ingestion
2. Factor evaluation
3. Strategic regime inference
4. Tactical confirmation
5. Advisory decision and reporting
6. Confidence calibration and validation

The execution layer becomes optional and external. It is no longer part of the core recommendation pipeline.

## Proposed Module Layout

```text
src/
  strategy/
    factor_registry.py
    factor_models.py
    strategic_engine.py
    tactical_engine.py
    advisory_engine.py
    reporting.py
  indicators/
    technical.py
    valuation.py
    macro_liquid.py
    sentiment_cycle.py
    miner_cycle.py
  backtest/
    advisory_backtest.py
    datasets.py
    metrics.py
    calibration.py
```

## Core Domain Model

### `FactorDefinition`

`FactorDefinition` is the metadata contract for each factor.

Required fields:

- `name`
- `layer`
- `block`
- `source_class`
- `is_required_for_add`
- `is_required_for_reduce`
- `is_backtestable`
- `freshness_ttl_hours`
- `default_weight`
- `confidence_class`

Example blocks:

- `valuation`
- `trend_cycle`
- `macro_liquidity`
- `sentiment_tactical`
- `market_structure`

### `FactorObservation`

`FactorObservation` is the runtime output of a factor calculation.

Required fields:

- `name`
- `score`
- `is_valid`
- `details`
- `description`
- `timestamp`
- `freshness_ok`
- `confidence_penalty`
- `blocked_reason`

`FactorObservation` replaces the current minimal `IndicatorResult` contract as the primary advisory data type.

### `Recommendation`

`Recommendation` is the top-level output object.

Required fields:

- `action`
- `confidence`
- `strategic_regime`
- `tactical_state`
- `supporting_factors`
- `conflicting_factors`
- `missing_required_blocks`
- `missing_required_factors`
- `blocked_reasons`
- `summary`
- `calibration_context`

## Factor Registry Design

`factor_registry.py` becomes the single source of truth for:

- which factors exist
- which layer they belong to
- which evidence block they represent
- whether they are allowed in production
- whether they are replayable in backtests
- whether they are required for `ADD` or `REDUCE`

This removes hidden policy drift between:

- indicator code
- strategy policy constants
- reporting
- backtest assumptions

## Recommended Production Factor Set

### Strategic production factors

- `MVRV_Proxy`
  - keep for now, but low confidence class compared with a true realized-cap measure
- `Puell_Multiple`
- `Hash_Ribbon`
- `200WMA`
- `Cycle_Pos`
- `Net_Liquidity`
- `Yields_Regime`
- `DXY_Regime`

### Tactical production factors

- `RSI_Div`
- `FearGreed`
- `Short_Term_Stretch`

### Research-only factors

- `Production_Cost`
- `Options_Wall`
- `ETF_Flow`
- any funding or open-interest factor without durable free replay

## Decision Architecture

### Step 1: Evaluate all factors

Each indicator returns a `FactorObservation`.

No factor may decide the action by itself.

### Step 2: Partition factors by block

The engine groups valid observations into independent blocks:

- valuation
- trend_cycle
- macro_liquidity
- sentiment_tactical
- market_structure

This is where the system prevents double-counting.

### Step 3: Compute strategic regime

The strategic engine only sees slow factors:

- valuation
- trend_cycle
- macro_liquidity

Output:

- `BULLISH_ACCUMULATION`
- `NEUTRAL`
- `OVERHEATED`
- `RISK_OFF`
- `INSUFFICIENT_DATA`

The strategic engine is responsible for regime, not action.

### Step 4: Compute tactical state

The tactical engine only sees:

- tactical sentiment
- tactical stretch
- any approved short-horizon market-structure factor

Output:

- `FAVORABLE_ADD`
- `NEUTRAL`
- `FAVORABLE_REDUCE`
- `INSUFFICIENT_DATA`

The tactical engine refines timing. It cannot overturn a structurally blocked regime.

### Step 5: Apply action gates

`advisory_engine.py` maps strategic regime and tactical state into action eligibility.

### `ADD` gate

`ADD` is eligible only if all of the following are true:

- strategic coverage is at or above threshold
- required blocks for `ADD` are present
- valuation or recovery evidence is bullish
- macro block is not bearish
- trend block is not bearish
- conflict count stays within threshold
- confidence can be calibrated into an actionable band

### `REDUCE` gate

`REDUCE` is eligible only if all of the following are true:

- strategic coverage is at or above threshold
- required blocks for `REDUCE` are present
- overheating or deterioration evidence exists
- at least one non-price block confirms the risk
- tactical state is not strongly favorable to add
- confidence can be calibrated into an actionable band

### `HOLD`

Return `HOLD` when:

- coverage is adequate
- no action gate is satisfied

### `INSUFFICIENT_DATA`

Return `INSUFFICIENT_DATA` when:

- required blocks are missing
- freshness rules fail for required factors
- required strategic coverage is not met

## Confidence Model

Confidence is computed after the action gate succeeds and is then calibrated against historical performance.

Base confidence inputs:

- strategic coverage
- required-block completeness
- factor freshness
- block agreement
- conflict penalty
- factor confidence class
- historical precision table
- horizon-specific calibration curve

Recommended confidence bands:

- `80-100`: high conviction
- `60-79`: actionable but contested
- `<60`: downgrade to `HOLD` unless the action is `INSUFFICIENT_DATA`

Calibration requirements:

- confidence must not collapse to a single value across the full backtest
- higher confidence buckets must not be less precise than lower confidence buckets on the same horizon
- 84-day and 182-day calibration should matter more than 28-day calibration for cycle decisions

This keeps low-quality signals from being labeled as strong advice.

## Reporting Model

`reporting.py` should produce a report that is explicit about blocked actions.

Required report sections:

- recommendation summary
- confidence
- strategic regime
- tactical state
- supporting factors
- conflicting factors
- missing required factors
- missing required blocks
- freshness warnings
- excluded research factors

The report must distinguish between:

- `HOLD because evidence is mixed`
- `INSUFFICIENT_DATA because evidence is incomplete`

Those are not the same operationally.

## Backtest Architecture

The backtest must be rebuilt as an advisory-quality evaluator.

`advisory_backtest.py` should not treat portfolio return as the primary acceptance metric.

Primary outputs:

- forward 4-week return by action bucket
- forward 12-week return by action bucket
- forward 26-week return by action bucket
- `ADD` precision
- `REDUCE` precision
- false-positive rate
- false-negative rate
- confidence-bucket monotonicity
- calibration curves by confidence bucket
- cycle-sliced summary tables

Secondary outputs:

- optional long/flat portfolio simulation for context only

This keeps validation aligned with the target product.

## Data Policy

The architecture keeps the existing free-data rule and formalizes it at the registry layer.

A factor may enter production only if:

- live data is free
- historical replay is free
- parsing is stable enough for unattended use
- data freshness is acceptable for the factor horizon

If any of those fail, the factor is research-only.

## Migration Plan

### Phase 1: Policy and models

- add `factor_registry.py`
- add `factor_models.py`
- define factor metadata
- define recommendation data model

### Phase 2: Decouple execution state

- isolate or deprecate `ExecutionEngine`
- remove `StateTracker` from the advisory path
- stop using budget fields in recommendation logic

### Phase 3: Implement new factor block logic

- add `Hash_Ribbon`
- add `DXY_Regime`
- convert `Yields` into regime logic
- add `Short_Term_Stretch`
- remove or reclassify `Pi_Cycle`

### Phase 4: Implement advisory engine

- strategic regime logic
- tactical state logic
- action gates
- confidence scoring
- blocked-reason reporting

### Phase 5: Replace acceptance backtest

- add advisory metrics
- add confidence calibration
- regenerate artifacts
- document cycle-sliced, walk-forward, and horizon-specific results

## Risks and Trade-Offs

### Risk: fewer actions

A fail-closed engine will produce fewer `ADD` and `REDUCE` actions.

This is acceptable. The target is high-confidence advice, not frequent advice.

### Risk: underfitting

Block-based gates may appear too conservative at first.

This is preferable to an overfit score blender, especially in Bitcoin where correlated signals can create false confidence.

### Risk: free-data limits

Some desirable market-structure factors may remain research-only.

The architecture is designed to tolerate this by making missing blocks explicit instead of silently substituting weak proxies.

## Rejected Alternatives

### 1. Keep the current layered system and only tune thresholds

Rejected because the main problem is not threshold calibration. The main problem is invalid architecture boundaries and missing action gates.

### 2. Keep budget logic but hide it behind the report

Rejected because hidden execution assumptions still contaminate advice quality.

### 3. Flat weighted average with more factors

Rejected because it increases apparent complexity without increasing independent evidence.

## Acceptance Conditions for Implementation

The implementation based on this ADD is accepted only if:

- the core advisory path is stateless
- `ADD` and `REDUCE` both require explicit block-level coverage
- `INSUFFICIENT_DATA` is reachable and tested
- current stale backtest artifacts are replaced
- advisory metrics become the primary validation artifact
- confidence is calibrated and demonstrably monotonic by bucket on at least one holdout slice
- longer-horizon precision is evaluated alongside 28-day precision
- docs and code policy stay aligned

## Deliverable

This ADD is the architectural blueprint for the advisory refactor defined in the SRD.

It is intended to be followed by an implementation plan, then code changes.
