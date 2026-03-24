# BTC Monitor ADD: Backtest Performance Calibration Architecture

> **For Claude Code:** This ADD defines the architecture changes required to improve advisory backtest quality. The current system is structurally sound, but the backtest evidence does not yet support high-confidence sign-off. The main problem is not statelessness anymore; it is calibration, sample quality, and decision precision. Do not reintroduce execution state, budget pacing, or auto-trading into the core advisory path.

## Metadata

- Status: Proposed
- Date: 2026-03-24
- Type: Architecture design and decision document
- Scope: Backtest performance, confidence calibration, horizon-aware validation, false-positive reduction
- Parent context: `docs/2026-03-23-btc-monitor-high-confidence-advisory-srd.md`

## Executive Decision

The advisory engine will be refined into a **calibrated backtest-driven decision system** whose primary purpose is to improve the quality of `ADD` and `REDUCE` recommendations.

The current architecture already emits stateless advice. The remaining work is to make that advice materially better by:

- tightening gate logic where false positives are concentrated
- calibrating confidence against empirical outcomes
- requiring minimum sample support before claiming a horizon result
- evaluating performance by regime, not only by aggregate precision
- separating genuine evidence from proxy-only convenience features

This ADD does **not** change the system into a trading engine. It remains an advisory system.

## Current Baseline

The current committed backtest shows:

- `450` weeks of history
- `ADD` frequency around `17%`
- `REDUCE` frequency around `0.2%`
- `ADD` precision around `1.3%` across `28d`, `84d`, and `182d`
- `REDUCE` precision reported as `100%` across all horizons, but based on only `1` sample
- persistent `ADD` false positives across all horizons

Interpretation:

- `ADD` is far too noisy to claim high confidence
- `REDUCE` may be directionally correct, but the sample size is too small to be statistically persuasive
- confidence is not yet calibrated enough to distinguish strong from weak setups

## Design Goals

- improve `ADD` precision materially
- retain or improve `REDUCE` precision with more samples
- reduce confidence saturation
- keep the advisory path stateless
- preserve fail-closed behavior when evidence is incomplete
- make the backtest reproducible and sample-aware
- ensure each recommendation can be explained by evidence blocks

## Non-Goals

- no portfolio sizing
- no capital budgeting
- no monthly execution state
- no auto-order placement
- no external paid data dependency
- no exact top/bottom forecasting

## Problem Analysis

### 1. `ADD` is over-triggering on weak confluence

The current `ADD` gate still allows too many recoveries and bottoms to pass with insufficient quality control.

Main issue:

- valuation and trend can both be favorable while macro is still unresolved
- evidence overload bypasses some vetoes
- the confidence number can look stronger than the real forward outcome

### 2. `REDUCE` has too few observations

The current `REDUCE` result is not robust because the signal is rare.

Main issue:

- one or a few correct calls can produce a perfect precision number
- that number is not stable enough for sign-off
- the engine needs more sampled overheating regimes or stricter admission logic to make the metric meaningful

### 3. Confidence saturates too easily

Confidence should reflect uncertainty, not just block count.

Main issue:

- too many aligned factors produce a near-fixed high confidence
- confidence does not yet incorporate sample support, disagreement severity, or historical calibration

### 4. Backtest evaluation is horizon-agnostic in practice

Even though the report tracks `28d`, `84d`, and `182d`, the system does not yet optimize explicitly for horizon-specific tradeoffs.

Main issue:

- short-horizon labels can punish slow cycle signals
- long-horizon labels can hide near-term false positives
- the correct fix is multi-horizon calibration, not choosing one horizon and ignoring the others

## Proposed Architecture

### 1. Calibration Layer

Add a calibration layer between raw recommendation rules and the final confidence output.

Responsibilities:

- map raw evidence strength to calibrated confidence buckets
- penalize weak or conflict-heavy signals
- reduce confidence when sample support is sparse
- cap confidence when the historical bucket has unstable outcomes

Inputs:

- action
- regime
- block agreement
- freshness
- conflict count
- historical bucket statistics

Outputs:

- calibrated confidence score
- confidence bucket
- calibration context used in the report

### 2. Horizon-Aware Scoring

Each advisory call must be scored against multiple forward horizons.

Required horizons:

- `28d`
- `84d`
- `182d`

The architecture should:

- treat `28d` as responsiveness
- treat `84d` as core medium-term validation
- treat `182d` as cycle confirmation

Decision quality should not be judged by one horizon alone.

### 3. Regime-Conditioned Gates

Action gates must be regime-aware.

For `ADD`:

- require strong valuation and trend support
- require macro not to be in hard conflict unless evidence overload is real
- require minimum block agreement
- reject low-support recoveries

For `REDUCE`:

- require overheating plus a real breakdown confirmation
- require tactical evidence to stop being strongly bullish
- require enough historical examples before claiming confidence in a bucket

### 4. Sample-Aware Acceptance

Any reported precision must include sample counts.

The architecture must distinguish:

- no samples
- one sample
- small sample
- adequate sample

The report should not treat these states as equivalent.

### 5. False-Positive Diagnosis

The backtest report must explain where the engine fails.

Required slices:

- by action
- by horizon
- by regime
- by confidence bucket
- by year or cycle phase

This is necessary because a flat aggregate precision number hides the actual failure mode.

## Recommended Module Changes

### `src/backtest/advisory_backtest.py`

Add:

- sample-count-aware report generation
- confidence bucket aggregation
- action-by-regime breakdown
- false-positive and false-negative slices
- optional backtest artifact output directory

### `src/strategy/advisory_engine.py`

Add:

- calibrated confidence output
- bucket-level sample awareness
- stricter `ADD` admission
- stricter `REDUCE` admission

### `src/strategy/strategic_engine.py`

Add:

- explicit support for a regime confidence value
- clearer distinction between `NEUTRAL` and `INSUFFICIENT_DATA`
- optional evidence-strength summary for downstream calibration

### `src/strategy/reporting.py`

Add:

- calibration context
- confidence bucket statistics
- sample counts per horizon
- false-positive and false-negative summaries

### `src/backtest/metrics.py`

Add:

- horizon-specific precision with counts
- confidence bucket evaluation
- action/regime cross tabs
- explicit support for “insufficient sample” states

## Calibration Principles

### 1. Confidence must be monotonic but not saturating

More agreement should generally increase confidence.

But:

- confidence must not jump to 100 simply because more factors are present
- confidence should plateau when evidence quality is weak
- confidence should decline when the historical bucket has unstable precision

### 2. Hard conflicts should matter more than soft support

A single hard contradiction should matter more than three weak supporting signals.

### 3. The engine should prefer `HOLD` when uncertain

The target is high-confidence advisory quality, not maximum signal frequency.

### 4. Low-sample perfection is not a success condition

`REDUCE = 100%` with one sample is not proof.

The architecture must require a minimum sample count before a performance claim is considered valid.

## Migration Plan

### Phase 1: Measure

- regenerate the backtest artifact
- add sample counts to every metric
- publish current bucket quality without changing decision logic

### Phase 2: Calibrate

- add confidence bucket mapping
- penalize weakly supported `ADD` cases
- preserve `REDUCE` only when breakdown confirmation is real

### Phase 3: Tighten

- reduce `ADD` false positives
- add stronger vetoes where confidence is misleading
- refine strategic and tactical thresholds using historical slices

### Phase 4: Validate

- rerun the full historical backtest
- compare old vs new precision by horizon
- require sample thresholds before sign-off

## Risks

- overfitting to a limited BTC history
- improving precision at the cost of missing good accumulation opportunities
- using a single impressive metric to hide low support
- making confidence look better without changing underlying edge

## Acceptance Criteria

The design is acceptable only if:

- `ADD` precision improves materially and is supported by enough samples
- `REDUCE` remains strong with meaningful sample support
- confidence buckets are calibrated to historical outcomes
- the report includes sample counts and false-positive slices
- the engine remains stateless and advisory-only

