# BTC Monitor SPR: Backtest Performance Requirements

> **For Claude Code:** This SPR turns the backtest performance improvement problem into implementable requirements. The goal is not just to make the report look better. The goal is to make the advisory system measurably more useful, more calibrated, and harder to overclaim. Development must use strict TDD and subagent-driven execution.

## Metadata

- Status: Proposed
- Date: 2026-03-24
- Type: System Performance Requirements
- Parent ADD: `docs/2026-03-24-btc-monitor-backtest-performance-add.md`

## Purpose

This document defines the requirements for improving advisory backtest performance.

The current system is operational, reproducible, and stateless. What remains is performance quality:

- `ADD` precision is too low
- `REDUCE` sample support is too small
- confidence is not yet calibrated enough
- the report does not yet prove high-confidence usefulness

## Mandatory Development Process

These process rules are part of the requirement set.

### P-1 Strict TDD

All implementation must follow strict TDD.

Required sequence:

1. write a failing test
2. verify the failure
3. implement the minimal fix
4. rerun the targeted test
5. rerun the relevant regression suite
6. refactor only when green

### P-2 Subagent-Driven Development

Independent performance tasks must be executed with subagents.

Required flow:

1. one subagent per independent task
2. one spec-compliance review
3. one code-quality review
4. no task is complete until both reviews pass

### P-3 Verification Before Completion

No performance claim may be made without a fresh verification command.

Required:

- exact command used
- actual exit code
- observed metric values

## System Goal

The target system must produce higher-quality BTC advisory output, measured by backtest performance and calibration quality.

The system remains advisory-only:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

The system must not:

- manage capital
- place orders
- use monthly budget pacing
- maintain execution state in the core decision path

## Functional Requirements

### FR-1 Backtest Artifact Must Be Reproducible

The backtest must be rerunnable from code and produce the committed artifacts.

Acceptance criteria:

- the backtest runner can write to an arbitrary output directory
- test runs do not overwrite production artifacts
- the report can be regenerated deterministically from the same inputs

Required tests:

- unit test using `tmp_path`
- artifact regeneration test

### FR-2 Precision Reporting Must Be Sample-Aware

Every precision value must be accompanied by its sample count.

Acceptance criteria:

- `ADD` and `REDUCE` precision are reported with counts
- zero-sample and one-sample cases are explicitly marked as insufficient evidence
- the report cannot imply statistical strength without a count

Required tests:

- report schema test
- sample-count rendering test

### FR-3 Minimum Sample Thresholds

The system must define minimum sample thresholds before making acceptance claims.

Acceptance criteria:

- `REDUCE` cannot be declared strong without minimum sample support
- `ADD` cannot be declared improved if the sample is too sparse
- threshold values are documented and enforced in tests

Required tests:

- threshold enforcement tests
- low-sample warning tests

### FR-4 Confidence Calibration

Confidence must be calibrated against historical outcomes.

Acceptance criteria:

- high confidence buckets must correspond to materially better historical precision
- confidence must not saturate solely because more factors are present
- confidence must vary when agreement quality changes

Required tests:

- monotonicity tests
- calibration bucket tests
- anti-saturation regression tests

### FR-5 ADD False-Positive Reduction

The system must reduce false positives for `ADD`.

Acceptance criteria:

- `ADD` false-positive count decreases versus the current baseline
- `ADD` precision improves meaningfully across at least one horizon
- improvement must not come from collapsing `ADD` frequency to zero

Required tests:

- regression test on representative false-positive cases
- comparison test against baseline metrics

### FR-6 REDUCE Sample Expansion or Conservative Labeling

The system must avoid overstating `REDUCE` quality.

Acceptance criteria:

- either `REDUCE` sample size increases enough for meaningful evaluation
- or the report clearly labels the sample as too small for strong claims
- a single sample cannot be used as proof

Required tests:

- sample-size labeling test
- low-support REDUCE report test

### FR-7 Multi-Horizon Evaluation

The backtest must evaluate at least `28d`, `84d`, and `182d` horizons.

Acceptance criteria:

- all three horizons are reported
- horizon-specific precision is visible
- horizon-specific false positives are visible

Required tests:

- horizon evaluation test
- horizon metric rendering test

### FR-8 Regime-Level Analysis

The report must break down results by strategic regime.

Acceptance criteria:

- report shows counts per regime
- report shows average confidence per regime
- report shows confidence spread if available

Required tests:

- regime breakdown rendering test
- confidence spread test

### FR-9 Error Analysis

The report must explain where the model fails.

Acceptance criteria:

- false-positive counts are shown per action and horizon
- false-positive samples can be traced to a timestamp
- report can distinguish weak performance from missing support

Required tests:

- false-positive table test
- sample traceability test

### FR-10 Dependency Isolation

The backtest test suite must not depend on live external services during collection.

Acceptance criteria:

- test collection succeeds without network access
- optional dependencies are lazy-loaded or abstracted behind test doubles
- the backtest path remains runnable in a clean CI environment

Required tests:

- collection test for backtest module
- dependency-free unit test using mocks

## Non-Functional Requirements

### NFR-1 Determinism

Given the same historical inputs, the backtest must produce the same result files.

### NFR-2 Interpretability

Every recommendation must be explainable in terms of blocks, conflict, and confidence context.

### NFR-3 Maintainability

Performance rules must be centralized rather than duplicated in tests, strategy code, and report generation.

### NFR-4 Safety

When evidence is weak, the system must prefer `HOLD`.

## Backtest Acceptance Gates

The next backtest run is acceptable only if all are true:

- artifacts are regenerated from code
- sample counts are present in the report
- `ADD` precision is better than the current baseline
- `REDUCE` is not overstated with trivial sample size
- false-positive analysis is included
- the test suite passes in a clean environment

## Traceability Matrix

| Requirement | Primary Test Area |
|-------------|------------------|
| FR-1 | backtest artifact tests |
| FR-2 | report schema tests |
| FR-3 | threshold tests |
| FR-4 | confidence calibration tests |
| FR-5 | false-positive regression tests |
| FR-6 | sample-support tests |
| FR-7 | horizon evaluation tests |
| FR-8 | regime breakdown tests |
| FR-9 | traceability and sample tests |
| FR-10 | dependency isolation tests |

## Recommended Implementation Tasks

### Story 1: Backtest artifact isolation

Tasks:

- add output directory support to the backtest runner
- update tests to use temporary directories
- verify production artifacts are not overwritten

### Story 2: Sample-aware reporting

Tasks:

- add counts to all precision metrics
- label low-sample metrics as unsupported
- render false-positive tables

### Story 3: Confidence calibration

Tasks:

- add confidence bucket analysis
- map historical precision to confidence buckets
- remove or reduce confidence saturation

### Story 4: ADD false-positive reduction

Tasks:

- identify the highest-frequency false-positive regimes
- tighten gates in those regimes
- add regression tests for those cases

### Story 5: REDUCE validation

Tasks:

- ensure the report does not overclaim from tiny sample size
- expand the sample if the market history supports it
- otherwise keep the result explicitly labeled as low-support

### Story 6: Clean environment verification

Tasks:

- lazy-load optional services
- mock data fetchers in tests
- make collection succeed without external APIs

## Required Verification Commands

The implementation is not complete until these commands are run successfully:

```bash
PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q
PYTHONPATH=. pytest tests/unit/strategy/test_advisory_engine_blocks.py tests/unit/strategy/test_confidence_scoring.py tests/unit/strategy/test_strategic_engine.py -q
PYTHONPATH=. pytest tests/unit
```

## Acceptance Summary

This SPR is satisfied only if the repository can show:

- reproducible backtest artifacts
- sample-aware precision reporting
- calibrated confidence
- materially improved `ADD` precision
- honest `REDUCE` reporting with adequate support
- clean test collection in the current environment

