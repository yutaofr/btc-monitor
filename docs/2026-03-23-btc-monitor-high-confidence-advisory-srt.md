# BTC Monitor SRT: System Requirements and Traceability

> **For Claude Code:** This SRT operationalizes the ADD in `docs/2026-03-23-btc-monitor-high-confidence-advisory-add.md`. Use it as the implementation contract. Development must run in strict TDD mode and subagent-driven mode. Do not write production code before a failing test exists. Do not claim completion without fresh verification evidence. The remaining implementation gap is calibration and horizon-aware validation, not statelessness.

## Metadata

- Status: Proposed
- Date: 2026-03-23
- Parent ADD: `docs/2026-03-23-btc-monitor-high-confidence-advisory-add.md`
- Parent SRD: `docs/2026-03-23-btc-monitor-high-confidence-advisory-srd.md`
- Scope: Functional requirements, non-functional requirements, calibration requirements, traceability, and acceptance-test contract

## Purpose

This SRT converts the ADD into:

- implementable system requirements
- explicit acceptance criteria
- required test coverage
- requirement-to-test traceability

This document is intentionally strict. The target product is a high-confidence BTC advisory engine. Weakly tested behavior is not acceptable.

## Mandatory Development Process

These process rules are requirements, not suggestions.

### Process Requirement P-1: Strict TDD

All implementation work must use strict TDD.

Required mode:

- write one failing test first
- verify the failure is the intended failure
- write the minimum code to pass
- rerun the targeted test
- rerun broader regression tests
- refactor only after green

Forbidden:

- writing production code before a failing test exists
- writing speculative implementation and adding tests later
- claiming a regression test exists without proving red-to-green behavior

### Process Requirement P-2: Subagent-Driven Development

All implementation work against the approved plan must use subagent-driven execution for task-level delivery whenever tasks are independent enough to delegate.

Required mode:

- one implementation subagent per task
- one spec-compliance review after the implementation step
- one code-quality review after spec compliance passes
- no task is complete until both reviews pass

Forbidden:

- batching multiple loosely specified tasks into one implementation step
- skipping review passes
- starting the next task while a current task has open review findings

### Process Requirement P-3: Verification Before Completion

No completion claim is valid without fresh verification evidence.

Required mode:

- run the exact verification command for the claim
- inspect output and exit code
- report the actual result

Forbidden:

- "should pass"
- "looks done"
- "probably fixed"
- claiming acceptance without a fresh command run

## System Scope

The target system must emit advice only:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

The target system must not:

- manage budget
- manage monthly execution state
- size positions
- auto-execute orders

## Functional Requirements

## FR-1 Advisory Output Contract

The system must return a structured recommendation object.

Minimum required fields:

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

Acceptance criteria:

- any successful recommendation call returns the full object
- all four actions are representable
- output schema is stable in both live and backtest paths

Required tests:

- unit tests for recommendation serialization and schema completeness
- regression tests for each action type

## FR-2 Stateless Core Advisory Path

The core advisory decision path must be stateless.

Acceptance criteria:

- core advisory logic does not depend on `StateTracker`
- core advisory logic does not read budget or monthly execution fields
- advisory result for the same inputs is deterministic

Required tests:

- unit tests proving advisory engine works with pure input observations only
- grep-based or architectural tests preventing imports from execution-state modules in the advisory path

## FR-3 Factor Registry as Policy Source of Truth

The system must define factor metadata in a central registry.

Required registry attributes:

- factor name
- layer
- evidence block
- production eligibility
- backtest eligibility
- `ADD` requirement flag
- `REDUCE` requirement flag
- freshness TTL
- confidence class

Acceptance criteria:

- policy constants are not duplicated across strategy, reporting, and backtest
- factor metadata is queryable from one module

Required tests:

- unit tests for registry completeness and uniqueness
- tests that all production factors have required metadata

## FR-4 Independent Evidence Blocks

The advisory engine must reason in evidence blocks, not a flat factor list.

Minimum production blocks:

- `valuation`
- `trend_cycle`
- `macro_liquidity`
- `sentiment_tactical`
- `market_structure` when available

Acceptance criteria:

- the engine groups valid factors by block
- multiple price-location factors cannot be counted as separate blocks

Required tests:

- unit tests proving block partitioning
- regression tests proving correlated factors do not inflate block count

## FR-5 Strategic Regime Engine

The strategic engine must infer regime from slow factors only.

Allowed strategic inputs:

- valuation block
- trend_cycle block
- macro_liquidity block

Required outputs:

- `BULLISH_ACCUMULATION`
- `NEUTRAL`
- `OVERHEATED`
- `RISK_OFF`
- `INSUFFICIENT_DATA`

Acceptance criteria:

- tactical factors cannot directly change strategic regime
- missing required strategic evidence can produce `INSUFFICIENT_DATA`

Required tests:

- unit tests for all regime states
- tests proving tactical inputs are ignored by the strategic engine

## FR-6 Tactical Confirmation Engine

The tactical engine must evaluate short-horizon confirmation only.

Minimum tactical factors:

- `RSI_Div`
- `FearGreed`
- `Short_Term_Stretch`

Required outputs:

- `FAVORABLE_ADD`
- `NEUTRAL`
- `FAVORABLE_REDUCE`
- `INSUFFICIENT_DATA`

Acceptance criteria:

- tactical logic can refine timing
- tactical logic cannot create structural conviction alone

Required tests:

- unit tests for tactical-state transitions
- tests proving tactical-only bullish inputs cannot trigger `ADD`

## FR-7 `ADD` Gate

The advisory engine must gate `ADD` through explicit rule checks.

Minimum `ADD` requirements:

- coverage threshold met
- required blocks for `ADD` present
- valuation or recovery evidence bullish
- macro block not bearish
- trend block not bearish
- conflict count within threshold

Acceptance criteria:

- a one-factor bullish scenario cannot return `ADD`
- missing required block returns `INSUFFICIENT_DATA`, not `HOLD`

Required tests:

- unit tests for successful `ADD`
- unit tests for blocked `ADD`
- adversarial regression test for one-factor bullish false positive

## FR-8 `REDUCE` Gate

The advisory engine must gate `REDUCE` through explicit rule checks.

Minimum `REDUCE` requirements:

- coverage threshold met
- required blocks for `REDUCE` present
- overheating or deterioration evidence present
- at least one non-price block confirms the risk
- tactical state is not strongly favorable to add

Acceptance criteria:

- a one-factor overheated scenario cannot return `REDUCE`
- pure price-location overheating without non-price confirmation cannot return `REDUCE`

Required tests:

- unit tests for successful `REDUCE`
- unit tests for blocked `REDUCE`
- adversarial regression test for one-factor overheated false positive

## FR-9 `HOLD` and `INSUFFICIENT_DATA` Distinction

The system must distinguish mixed evidence from missing evidence.

Acceptance criteria:

- `HOLD` means coverage is adequate but no action gate passed
- `INSUFFICIENT_DATA` means required evidence was missing or stale

Required tests:

- unit tests for both states
- reporting tests proving blocked reasons are explicit

## FR-10 Confidence Model

The system must compute confidence from evidence quality.

Minimum confidence inputs:

- strategic coverage
- required-block completeness
- freshness status
- block agreement
- conflict penalty
- factor confidence class
- historical precision by bucket
- horizon-specific correctness

Acceptance criteria:

- confidence is deterministic for a fixed input set
- low-quality evidence cannot produce a high-confidence recommendation
- recommendations below the configured action threshold are downgraded to `HOLD`, unless blocked into `INSUFFICIENT_DATA`
- confidence must not collapse to a single repeated value across the full-history backtest
- higher confidence buckets must not have lower precision than lower buckets on the same evaluation horizon
- 84-day and 182-day calibration must be preferred over 28-day calibration when the product is judging BTC cycle advice

Required tests:

- unit tests for confidence-band behavior
- monotonicity tests for increasing evidence quality
- calibration tests that compare bucket precision across horizons

## FR-11 Reporting

The system must produce explicit advisory reports.

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

Acceptance criteria:

- report distinguishes `HOLD` from `INSUFFICIENT_DATA`
- report does not imply actionability when required evidence is missing

Required tests:

- golden-file or snapshot tests for representative reports
- unit tests for blocked-reason rendering

## FR-12 Backtest Alignment

The backtest must validate advisory quality, not only portfolio return.

Required outputs:

- forward 4-week returns by action bucket
- forward 12-week returns by action bucket
- forward 26-week returns by action bucket
- `ADD` precision
- `REDUCE` precision
- false-positive and false-negative rates
- confidence-bucket monotonicity
- calibration curves by confidence bucket
- cycle-sliced summaries

Acceptance criteria:

- backtest output schema matches current code
- committed artifacts are generated by current code
- live policy and backtest policy share the same registry-driven factor definitions
- 28-day, 84-day, and 182-day results are all present in the validation artifact
- 84-day and 182-day precision are treated as primary acceptance signals for cycle advice

Required tests:

- parity tests for registry and advisory outputs
- artifact schema tests
- regression tests for metric calculation

## FR-14 Confidence Calibration

The system must calibrate recommendation confidence against historical advisory quality.

Required behavior:

- confidence buckets must be derivable from the backtest artifact
- confidence must be monotonic with historical precision on validation slices
- confidence should not saturate across the full history unless the model is genuinely uniform
- calibration must be reproducible from committed code and committed data

Acceptance criteria:

- a confidence bucket table exists for each required horizon
- higher bucket precision is greater than or equal to lower bucket precision, within an allowed tolerance
- the calibration artifact is regenerated from current code

Required tests:

- calibration unit tests
- monotonic bucket precision tests
- regression tests that fail if all recommendations collapse into one confidence value

## FR-15 Multi-Horizon Validation Policy

The system must validate advisory quality on multiple forward horizons.

Required horizons:

- 28 days
- 84 days
- 182 days

Required behavior:

- 28-day precision is diagnostic
- 84-day and 182-day precision are primary validation signals for cycle advice
- the same recommendation row must be evaluable across all required horizons

Acceptance criteria:

- every backtest artifact includes the required horizons
- the report clearly labels the primary and diagnostic horizons
- acceptance does not rely on a single horizon alone

Required tests:

- horizon schema tests
- per-horizon precision tests
- report tests proving primary versus diagnostic horizon labeling

## FR-13 Free-Data Enforcement

A factor may enter production only if:

- live data is free
- historical replay is free
- parsing is stable
- freshness is acceptable for the factor horizon

Acceptance criteria:

- any factor failing one of the above is research-only
- research-only factors do not influence action gates

Required tests:

- registry tests for production eligibility flags
- regression tests proving research-only factors cannot change action outcome

## Non-Functional Requirements

## NFR-1 Determinism

For fixed factor observations, the advisory engine must return the same output every run.

Required tests:

- deterministic unit tests with fixed fixture inputs

## NFR-2 Explainability

Each recommendation must be explainable from explicit factor evidence and blocked reasons.

Required tests:

- report and recommendation snapshot tests

## NFR-3 Policy Consistency

The system must not drift between:

- factor policy
- reporting policy
- backtest policy

Required tests:

- shared-policy parity tests against the registry

## NFR-4 Conservative Failure Mode

Missing required production data must fail closed.

Required tests:

- unit tests for missing macro blocks
- unit tests for stale required factors

## Requirement Traceability Matrix

| Requirement | ADD Section | Primary Tests | Acceptance Gate |
| --- | --- | --- | --- |
| `FR-1` Advisory output contract | Core Domain Model | schema tests, action regression tests | all actions + full payload |
| `FR-2` Stateless core path | Architecture Principles | isolation tests, import-boundary tests | no execution-state dependency |
| `FR-3` Factor registry | Factor Registry Design | registry completeness tests | one policy source |
| `FR-4` Independent evidence blocks | Decision Architecture | block partition tests | no double-counting |
| `FR-5` Strategic regime engine | Decision Architecture | regime unit tests | tactical cannot set regime |
| `FR-6` Tactical engine | Decision Architecture | tactical-state tests | tactical cannot force structure |
| `FR-7` `ADD` gate | Decision Architecture | gate tests, false-positive regression tests | no one-factor `ADD` |
| `FR-8` `REDUCE` gate | Decision Architecture | gate tests, false-positive regression tests | no one-factor `REDUCE` |
| `FR-9` `HOLD` vs `INSUFFICIENT_DATA` | Reporting Model | state tests, report tests | semantic separation |
| `FR-10` Confidence model | Confidence Model | confidence tests | no weak-evidence high confidence |
| `FR-11` Reporting | Reporting Model | snapshot tests | explicit blocked reasons |
| `FR-12` Backtest alignment | Backtest Architecture | parity and schema tests | advisory-quality metrics |
| `FR-13` Free-data enforcement | Data Policy | eligibility and action-isolation tests | research-only cannot drive decisions |
| `FR-14` Confidence calibration | Confidence Calibration | calibration and monotonicity tests | confidence is bucket-calibrated |
| `FR-15` Multi-horizon validation | Multi-Horizon Validation Policy | horizon schema and precision tests | primary and diagnostic horizons are separated |

## Release Acceptance Gates

No implementation based on the ADD is accepted unless all gates below pass:

1. All unit tests pass.
2. All advisory gate regression tests pass.
3. All traceability rows in this SRT have implemented tests.
4. No stale backtest artifact remains in the committed acceptance set.
5. Backtest output schema matches current code.
6. `ADD` one-factor false-positive test passes.
7. `REDUCE` one-factor false-positive test passes.
8. Missing required-block tests return `INSUFFICIENT_DATA`.
9. Confidence calibration tests pass.
10. Multi-horizon validation tests pass.
11. Fresh verification commands were run before completion is claimed.

## Required Verification Commands

Minimum verification before claiming a phase is complete:

```bash
docker compose run --rm tests
docker compose run --rm app python -m src.backtest.advisory_backtest
```

If the backtest module name changes during implementation, the plan must update the command and preserve the verification requirement.

## Deliverable

This SRT is the requirements and test traceability contract for implementing the advisory architecture.
