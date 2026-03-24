# BTC Monitor SPT: Backtest Performance Implementation Plan

> **For Claude Code:** This SPT is the implementation plan for the backtest-performance improvements defined in `docs/2026-03-24-btc-monitor-backtest-performance-add.md` and `docs/2026-03-24-btc-monitor-backtest-performance-spr.md`. Development must use strict `test-driven-development`, `subagent-driven-development`, and `verification-before-completion`. No production code without a failing test first. No task is complete without fresh verification evidence.

**Goal:** Improve the advisory backtest so it produces more reliable `ADD` / `REDUCE` recommendations, calibrated confidence, sample-aware reporting, and honest performance claims.

**Scope:** backtest reproducibility, confidence calibration, false-positive reduction, sample-aware metrics, regime-level analysis, and dependency isolation.

**Document position:** `ADD` defines the architecture, `SPR` defines the requirements, and this `SPT` defines the user stories and task execution plan.

---

## Delivery Rules

### Rule 1: TDD is mandatory

Every story and task must follow:

1. write a failing test
2. run it and confirm the intended failure
3. implement the minimum code to pass
4. rerun the target test
5. rerun broader regression tests
6. refactor only after green

### Rule 2: Subagent-driven execution is mandatory

Each independent task must be executed using:

1. one implementation subagent
2. one spec-compliance review
3. one code-quality review
4. one verification run before marking complete

Do not combine independent tasks into one implementation step if that weakens review quality.

### Rule 3: Acceptance tests are hard gates

A story is not complete because code exists. It is complete only when its explicit acceptance tests pass.

### Rule 4: Evidence before claims

Before claiming a story or phase is complete, run the verification commands for that scope and report the result.

---

## Story Map

### Epic 1: Backtest Reproducibility and Isolation

Purpose: make the backtest deterministic, rerunnable, and safe for tests.

### Epic 2: Sample-Aware Metrics and Honest Reporting

Purpose: ensure precision is reported with counts and unsupported sample sizes are labeled correctly.

### Epic 3: Confidence Calibration

Purpose: prevent confidence saturation and tie confidence to historical outcomes.

### Epic 4: ADD False-Positive Reduction

Purpose: reduce noisy `ADD` calls and improve precision without collapsing signal frequency.

### Epic 5: REDUCE Validation and Conservative Sign-Off

Purpose: avoid overstating `REDUCE` strength when sample support is too small.

### Epic 6: Regime and Error Analysis

Purpose: expose where the model fails by regime, horizon, and timestamp.

---

## Epic 1: Backtest Reproducibility and Isolation

### User Story 1.1

As a maintainer, I want the backtest to write to an arbitrary output directory so that tests do not overwrite production artifacts.

Acceptance criteria:

- backtest runner accepts `output_dir`
- tests use temporary directories
- committed artifacts are not overwritten by unit tests

Strict tests:

- `tmp_path` backtest test
- artifact overwrite regression test

Tasks:

- keep `output_dir` support in `src/backtest/advisory_backtest.py`
- update any remaining tests to use `tmp_path`
- add a regression test that proves production artifacts are untouched

### User Story 1.2

As a maintainer, I want the backtest module to collect cleanly in a minimal environment so that CI does not fail on optional services.

Acceptance criteria:

- backtest tests collect without requiring live services
- optional dependencies are lazy-loaded or mocked
- `fredapi` and similar optional imports do not block collection

Strict tests:

- collection test for `tests/unit/backtest/test_advisory_backtest.py`
- dependency isolation regression test

Tasks:

- lazy-load optional imports in `src/backtest/advisory_history.py`
- keep fetchers behind test doubles where possible
- add collection-focused regression tests

---

## Epic 2: Sample-Aware Metrics and Honest Reporting

### User Story 2.1

As a user, I want precision metrics with sample counts so that I can judge whether a result is statistically meaningful.

Acceptance criteria:

- precision table shows both rate and count
- zero-sample and one-sample buckets are labeled as unsupported
- the report cannot imply strong evidence without counts

Strict tests:

- report schema test
- sample-count rendering test
- low-sample labeling test

Tasks:

- extend `src/backtest/advisory_backtest.py` report generation
- add count columns for each action and horizon
- render explicit unsupported labels for small samples

### User Story 2.2

As a user, I want the report to include false-positive analysis so that precision failures are visible.

Acceptance criteria:

- false-positive counts are reported by action and horizon
- timestamps for representative false positives are included
- false-positive analysis is generated from the same artifact

Strict tests:

- false-positive table test
- representative timestamp test

Tasks:

- add false-positive slicing to the backtest report
- ensure the report renders a sample timestamp per failing bucket
- add tests for empty and non-empty false-positive slices

---

## Epic 3: Confidence Calibration

### User Story 3.1

As a user, I want confidence to reflect historical outcomes so that high scores actually mean stronger evidence.

Acceptance criteria:

- confidence is not saturated just because more factors align
- confidence varies with agreement quality and historical bucket quality
- confidence buckets correlate with better historical outcomes

Strict tests:

- confidence monotonicity test
- anti-saturation test
- calibration bucket test

Tasks:

- add calibration context to recommendation output
- revise confidence scoring in `src/strategy/advisory_engine.py`
- add bucket-based confidence evaluation in backtest metrics

### User Story 3.2

As a maintainer, I want confidence buckets tracked in the backtest so that calibration can be verified and tuned.

Acceptance criteria:

- confidence bucket statistics appear in the report
- each bucket has sample count and precision
- unsupported buckets are labeled clearly

Strict tests:

- confidence bucket report test
- bucket count test

Tasks:

- add confidence bucket aggregation to `src/backtest/metrics.py`
- render bucket statistics in the report
- update tests for bucket counts and labels

---

## Epic 4: ADD False-Positive Reduction

### User Story 4.1

As a user, I want `ADD` to be more selective so that accumulation signals are meaningful.

Acceptance criteria:

- `ADD` false-positive count drops versus the current baseline
- `ADD` precision improves on at least one horizon
- `ADD` frequency does not collapse to zero

Strict tests:

- baseline comparison test
- false-positive regression test for weak accumulation cases
- non-zero frequency guard test

Tasks:

- identify the highest-frequency `ADD` false-positive regimes
- tighten `ADD` gates where the error mass is concentrated
- keep evidence-overload logic but make it harder to trigger without support

### User Story 4.2

As a user, I want `ADD` confidence to be downgraded when evidence is weak so that weak recoveries do not look strong.

Acceptance criteria:

- weak evidence cannot produce high-confidence `ADD`
- confidence decreases when disagreement increases
- low-quality `ADD` cases fall back to `HOLD`

Strict tests:

- weak-evidence downgrade test
- disagreement penalty test

Tasks:

- tighten confidence-to-action coupling in `src/strategy/advisory_engine.py`
- add explicit downgrade rules for weak `ADD`
- add regression tests for downgrade behavior

---

## Epic 5: REDUCE Validation and Conservative Sign-Off

### User Story 5.1

As a reviewer, I want `REDUCE` to be reported conservatively so that one correct sample is not treated as proof.

Acceptance criteria:

- a single `REDUCE` sample cannot justify a strong sign-off claim
- report clearly states when `REDUCE` sample support is insufficient
- if `REDUCE` remains rare, the report must say so explicitly

Strict tests:

- low-sample `REDUCE` labeling test
- sign-off guard test

Tasks:

- add minimum-sample checks for `REDUCE`
- update report wording to reflect sample support
- prevent misleading “100% precision” claims on trivial samples

### User Story 5.2

As a user, I want `REDUCE` validation to include more than one horizon so that long-term and short-term correctness are both visible.

Acceptance criteria:

- `REDUCE` is evaluated at `28d`, `84d`, and `182d`
- horizon disagreement is visible in the report
- poor long-horizon support blocks strong claims

Strict tests:

- multi-horizon `REDUCE` test
- horizon disagreement report test

Tasks:

- keep multi-horizon evaluation in `src/backtest/advisory_backtest.py`
- render horizon-by-horizon `REDUCE` outcomes
- add regression coverage for horizon disagreement

---

## Epic 6: Regime and Error Analysis

### User Story 6.1

As a user, I want performance broken down by strategic regime so that I can see which regimes are reliable.

Acceptance criteria:

- report shows counts per strategic regime
- report shows average confidence per regime
- report shows spread or variability where available

Strict tests:

- regime breakdown report test
- confidence spread test

Tasks:

- keep regime aggregation in the backtest report
- add variability metrics to the output
- add regression tests for regime slices

### User Story 6.2

As a user, I want false positives traced to timestamps so that I can inspect regime-specific failures.

Acceptance criteria:

- false-positive examples include timestamps
- samples can be inspected by action and horizon
- report supports debugging of repeated failure modes

Strict tests:

- timestamp traceability test
- repeated-failure regression test

Tasks:

- preserve timestamps in report rows
- render representative false-positive timestamps
- add tests for traceability and repeated-failure buckets

---

## Recommended Execution Order

1. Backtest isolation and clean collection
2. Sample-aware reporting
3. Confidence calibration
4. ADD false-positive reduction
5. REDUCE conservative labeling
6. Regime and error analysis

---

## Verification Gates

No phase is complete until these commands are run successfully:

```bash
PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q
PYTHONPATH=. pytest tests/unit/strategy/test_advisory_engine_blocks.py tests/unit/strategy/test_confidence_scoring.py tests/unit/strategy/test_strategic_engine.py -q
PYTHONPATH=. pytest tests/unit
```

---

## Completion Criteria

The plan is complete only when:

- backtest artifacts are reproducible and isolated
- precision is reported with counts
- confidence is calibrated and non-saturating
- `ADD` precision improves materially
- `REDUCE` is labeled conservatively unless sample support is meaningful
- regime and failure analysis are present in the report
- all required tests pass under TDD and verification rules
