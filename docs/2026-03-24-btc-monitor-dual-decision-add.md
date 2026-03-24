# BTC Monitor ADD: Dual-Decision Advisory Architecture

> **For Claude Code:** This ADD implements the SRD in `docs/2026-03-24-btc-monitor-dual-decision-srd.md`. It keeps the system advisory-only and stateless, but splits the output into two independent decision branches: position adjustment and incremental cash deployment.

## Metadata

- Status: Proposed
- Date: 2026-03-24
- Parent: `docs/2026-03-24-btc-monitor-dual-decision-srd.md`

## Executive Decision

`btc-monitor` will expose two separate advisory engines:

1. `Position Advisory`
2. `Incremental Cash Advisory`

Both engines consume the same factor registry and observation model, but they use different labels, different benchmarks, and different acceptance criteria.

## Architectural Decision

### 1. Position Advisory Engine

This engine answers whether existing BTC exposure should be adjusted.

Output labels:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

Design rules:

- `ADD` requires strong long-horizon evidence plus tactical confirmation unless a tightly defined overload exception applies
- `REDUCE` requires overheating or deterioration evidence plus a non-price confirmation
- missing required blocks must fail closed
- confidence is calibrated from historical branch-specific outcomes

### 2. Incremental Cash Advisory Engine

This engine answers whether fresh capital should be deployed now.

Output labels:

- `BUY_NOW`
- `STAGGER_BUY`
- `WAIT`
- `INSUFFICIENT_DATA`

Design rules:

- `BUY_NOW` requires an attractive long-horizon entry regime and no strong short-term veto
- `STAGGER_BUY` is used when the long-horizon setup is favorable but the short-horizon setup is not clean enough for full conviction
- `WAIT` is the default when the entry is not clearly advantaged versus a benchmark buy
- the branch must compare against benchmark deployment paths, not just future return direction

## Shared Domain Model

### `FactorDefinition`

Keep the registry as the single source of truth for:

- factor name
- layer
- block
- source class
- required-for-add flag
- required-for-reduce flag
- required-for-buy-now flag
- required-for-wait veto
- backtestability
- freshness TTL
- weight
- confidence class

### `FactorObservation`

Each factor evaluation must include:

- `timestamp`
- `score`
- `is_valid`
- `details`
- `freshness_ok`
- `confidence_penalty`
- `blocked_reason`

### `Recommendation`

The output object must remain branch-specific and explicit.

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
- `freshness_warnings`
- `excluded_research_factors`
- `summary`

## Module Layout

```text
src/
  strategy/
    factor_models.py
    factor_registry.py
    strategic_engine.py
    tactical_engine.py
    position_advisory_engine.py
    incremental_buy_engine.py
    reporting.py
  backtest/
    advisory_backtest.py
    incremental_buy_backtest.py
    metrics.py
    calibration.py
```

## Branch Semantics

### Position Branch

This branch is conservative.

Its job is to avoid overtrading and preserve capital efficiency.

### Cash Branch

This branch is timing-sensitive.

Its job is to decide whether the current entry window is materially better than a simple benchmark.

That means the cash branch can be correct even when the position branch says `HOLD`.

## Calibration Strategy

Confidence must be branch-specific.

The system must not reuse one raw score across both branches because:

- a strong position-adjustment signal is not the same as a strong buy-timing signal
- the sample pools will differ
- the false-positive costs will differ
- the acceptable horizons will differ

Branch confidence must be mapped from historical calibration buckets.

## Reporting Strategy

The report must split clearly into:

- position advisory performance
- incremental cash advisory performance

Each report must include:

- action distribution
- horizon precision
- confidence bucket matrix
- false positive analysis
- false negative analysis
- regime breakdown
- sample counts

## Decision Principle

If the system cannot justify `BUY_NOW` with better-than-benchmark evidence, it must default to `STAGGER_BUY` or `WAIT`.

If the system cannot justify `ADD` or `REDUCE` with branch-specific evidence, it must default to `HOLD`.

## Why This Design

This separation is required because BTC investing has two different real-world questions:

- rebalancing an existing exposure
- deciding when new cash should enter

Combining those into one decision tree makes the model look stronger than it is and makes backtest interpretation ambiguous.

