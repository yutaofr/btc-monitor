# BTC Monitor High-Confidence Advisory Roadmap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Improve the advisory engine until its `ADD` / `REDUCE` recommendations are statistically credible, sample-aware, and calibrated enough to justify high-confidence use.

**Architecture:** Keep the system advisory-only and stateless. Improve signal quality by tightening `ADD` admission, making `REDUCE` sample support explicit, calibrating confidence from historical outcomes, and enforcing regime-level error analysis. The implementation must remain reproducible, test-first, and reviewable in small increments.

**Tech Stack:** Python 3.12, pandas, pytest, Docker, existing BTC indicator/fetcher stack

---

## Delivery Rules

### Rule 1: Strict TDD

Every task must follow:

1. write the failing test
2. run it and confirm it fails for the expected reason
3. implement the minimum code to pass
4. rerun the targeted test
5. rerun the relevant regression tests
6. refactor only after green

### Rule 2: Subagent-Driven Execution

Every independent task must use:

1. one implementation subagent
2. one spec-compliance review
3. one code-quality review
4. one verification run before marking complete

### Rule 3: Evidence Before Claims

No merge or sign-off claim is valid without fresh verification output from the canonical Docker command.

---

## Roadmap Summary

### Must-Fix

1. Make `ADD` materially more selective.
2. Make `REDUCE` sample support explicit and conservative.
3. Calibrate confidence against history instead of factor count.
4. Keep the calibration report complete and sample-aware.

### Should-Fix

5. Add regime-level error analysis to isolate where the model fails.
6. Improve factor quality where proxy signals are too coarse.
7. Keep the advisory path stateless and free of execution state.

### Acceptance Threshold

The engine is only “high-confidence” when:

- `ADD` precision improves materially versus the current baseline
- `REDUCE` has enough samples to support a real claim
- confidence buckets correlate with historical success
- false positives are lower and explainable by regime
- the report is sample-aware and honest about weak buckets

---

## Epic 1: Tighten `ADD`

### User Story 1.1

As a user, I want `ADD` to be harder to trigger so that accumulation signals are meaningful rather than noisy.

**Acceptance criteria**
- `ADD` false positives decrease versus the current baseline
- `ADD` precision improves on at least one horizon
- `ADD` frequency does not collapse to zero

**Files**
- Modify: `src/strategy/advisory_engine.py`
- Modify: `src/backtest/advisory_backtest.py`
- Test: `tests/unit/strategy/test_advisory_engine_blocks.py`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a regression test that reproduces a known weak `ADD` setup and asserts it must downgrade to `HOLD`.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_advisory_engine_blocks.py -k add -v`
Expected: fail on the weak-`ADD` scenario before the gating change.

**Step 3: Write minimal implementation**

Tighten the `ADD` gate by requiring stronger block agreement and narrower deep-value bypasses.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_advisory_engine_blocks.py -k add -v`
Expected: pass.

**Step 5: Commit**

```bash
git add src/strategy/advisory_engine.py tests/unit/strategy/test_advisory_engine_blocks.py
git commit -m "fix: tighten ADD admission"
```

### User Story 1.2

As a reviewer, I want the backtest to show whether the `ADD` change reduced false positives.

**Acceptance criteria**
- false-positive counts for `ADD` decrease or remain stable with better precision
- the report still includes counts and sample timestamps

**Files**
- Modify: `src/backtest/advisory_backtest.py`
- Modify: `data/backtest/advisory_performance_report.md`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a report assertion that the false-positive table still renders after the `ADD` gate change.

**Step 2: Run test to verify it fails**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -k false -v"`
Expected: fail if the report format regressed.

**Step 3: Write minimal implementation**

Keep the existing report format and regenerate the artifact only after the gate change is validated.

**Step 4: Run test to verify it passes**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q"`
Expected: pass.

**Step 5: Commit**

```bash
git add src/backtest/advisory_backtest.py data/backtest/advisory_performance_report.md tests/unit/backtest/test_advisory_backtest.py
git commit -m "fix: validate ADD backtest quality"
```

---

## Epic 2: Make `REDUCE` Honest

### User Story 2.1

As a user, I want `REDUCE` to be reported conservatively so that a one-sample win is not treated as evidence.

**Acceptance criteria**
- the report explicitly labels low-sample `REDUCE`
- no sign-off wording implies `REDUCE` is proven when support is tiny

**Files**
- Modify: `src/backtest/advisory_backtest.py`
- Modify: `data/backtest/advisory_performance_report.md`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a test that expects `Inadequate Sample (N=1)` for `REDUCE` and ensures the report renders it.

**Step 2: Run test to verify it fails**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -k reduce -v"`
Expected: fail if the low-sample label regresses.

**Step 3: Write minimal implementation**

Keep the sample-aware precision label logic and ensure `REDUCE` remains conservative.

**Step 4: Run test to verify it passes**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q"`
Expected: pass.

**Step 5: Commit**

```bash
git add src/backtest/advisory_backtest.py data/backtest/advisory_performance_report.md tests/unit/backtest/test_advisory_backtest.py
git commit -m "fix: keep REDUCE sample labeling conservative"
```

### User Story 2.2

As a maintainer, I want more `REDUCE` examples or stricter admission so the claim becomes statistically meaningful.

**Acceptance criteria**
- either `REDUCE` sample count increases meaningfully
- or the engine explicitly refuses to overclaim

**Files**
- Modify: `src/strategy/advisory_engine.py`
- Modify: `src/strategy/strategic_engine.py`
- Test: `tests/unit/strategy/test_advisory_engine_blocks.py`
- Test: `tests/unit/strategy/test_strategic_engine.py`

**Step 1: Write the failing test**

Add a test for an overheating scenario that should not emit `REDUCE` unless breakdown confirmation is real.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_strategic_engine.py tests/unit/strategy/test_advisory_engine_blocks.py -k reduce -v`
Expected: fail until the stricter gate is implemented.

**Step 3: Write minimal implementation**

Narrow the `REDUCE` gate to require clearer confirmation and keep tactical bullish conflict blocking intact.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_strategic_engine.py tests/unit/strategy/test_advisory_engine_blocks.py -q`
Expected: pass.

**Step 5: Commit**

```bash
git add src/strategy/advisory_engine.py src/strategy/strategic_engine.py tests/unit/strategy/test_advisory_engine_blocks.py tests/unit/strategy/test_strategic_engine.py
git commit -m "fix: tighten REDUCE proof standard"
```

---

## Epic 3: Calibrate Confidence

### User Story 3.1

As a user, I want confidence to reflect historical outcomes so that high values are actually trustworthy.

**Acceptance criteria**
- confidence buckets correlate with better historical precision
- confidence does not saturate just because more factors align
- confidence varies when conflict strength changes

**Files**
- Modify: `src/strategy/advisory_engine.py`
- Modify: `src/backtest/advisory_backtest.py`
- Test: `tests/unit/strategy/test_confidence_scoring.py`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a monotonicity test that distinguishes strong alignment from weak alignment and conflict.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_confidence_scoring.py -v`
Expected: fail on confidence saturation or weak separation.

**Step 3: Write minimal implementation**

Base confidence on block alignment, conflict penalties, and historical calibration buckets.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest tests/unit/strategy/test_confidence_scoring.py -q`
Expected: pass.

**Step 5: Commit**

```bash
git add src/strategy/advisory_engine.py tests/unit/strategy/test_confidence_scoring.py
git commit -m "fix: calibrate advisory confidence"
```

### User Story 3.2

As a reviewer, I want a complete confidence matrix so the report is honest about both present and absent buckets.

**Acceptance criteria**
- both `ADD` and `REDUCE` show bucket matrices
- zero-count rows are rendered explicitly
- the report remains stable as the sample mix changes

**Files**
- Modify: `src/backtest/advisory_backtest.py`
- Modify: `data/backtest/advisory_performance_report.md`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a regression test that checks both actions and all bucket rows are rendered, including zero-count rows.

**Step 2: Run test to verify it fails**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -k matrix -v"`
Expected: fail if the matrix is incomplete.

**Step 3: Write minimal implementation**

Render the full stable bucket matrix for both actions.

**Step 4: Run test to verify it passes**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q"`
Expected: pass.

**Step 5: Commit**

```bash
git add src/backtest/advisory_backtest.py data/backtest/advisory_performance_report.md tests/unit/backtest/test_advisory_backtest.py
git commit -m "fix: make confidence matrix complete"
```

---

## Epic 4: Improve Factor Quality

### User Story 4.1

As a maintainer, I want the weakest proxy factors identified so that future work targets actual signal quality.

**Acceptance criteria**
- false positives are grouped by regime and horizon
- the worst failure clusters are visible
- the factor mix is inspectable, not just the output

**Files**
- Modify: `src/backtest/advisory_backtest.py`
- Modify: `src/strategy/reporting.py`
- Test: `tests/unit/backtest/test_advisory_backtest.py`

**Step 1: Write the failing test**

Add a report assertion for the false-positive table and regime breakdown sections.

**Step 2: Run test to verify it fails**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -k false -v"`
Expected: fail if the error analysis regresses.

**Step 3: Write minimal implementation**

Keep and expand the current false-positive sections without changing the advisory semantics.

**Step 4: Run test to verify it passes**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit/backtest/test_advisory_backtest.py -q"`
Expected: pass.

**Step 5: Commit**

```bash
git add src/backtest/advisory_backtest.py src/strategy/reporting.py tests/unit/backtest/test_advisory_backtest.py
git commit -m "fix: expand backtest error analysis"
```

### User Story 4.2

As a maintainer, I want to replace coarse proxies where they are clearly limiting precision.

**Acceptance criteria**
- proxy-heavy factors are identified
- replacements are tested before being adopted

**Files**
- Modify: `src/indicators/valuation.py`
- Modify: `src/indicators/technical.py`
- Test: `tests/unit/test_technical_indicators.py`

**Step 1: Write the failing test**

Add a test for the improved factor behavior you want to replace the proxy with.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest tests/unit/test_technical_indicators.py -v`
Expected: fail until the new logic is present.

**Step 3: Write minimal implementation**

Implement the smallest factor improvement that supports the new test.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest tests/unit/test_technical_indicators.py -q`
Expected: pass.

**Step 5: Commit**

```bash
git add src/indicators/valuation.py src/indicators/technical.py tests/unit/test_technical_indicators.py
git commit -m "fix: improve factor quality"
```

---

## Epic 5: Final Verification

### User Story 5.1

As a reviewer, I want a fresh sandboxed verification run so that the final merge decision is evidence-based.

**Acceptance criteria**
- canonical Docker unit suite passes
- regenerated report matches the new behavior
- merge caveat remains honest about sample limitations

**Files**
- Modify: `data/backtest/advisory_performance_report.md`
- Test: none new; run verification commands

**Step 1: Run the verification command**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. pytest tests/unit -q"`
Expected: pass.

**Step 2: Regenerate the backtest artifact**

Run: `docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install -r requirements.txt >/tmp/pip.log && PYTHONPATH=. python -m src.backtest.advisory_backtest"`
Expected: report and CSV regenerate successfully.

**Step 3: Review the metrics**

Confirm:

- `ADD` precision is materially improved
- `REDUCE` is not overstated with tiny sample support
- false positives are lower and explainable

**Step 4: Commit**

```bash
git add data/backtest/advisory_performance_report.md
git commit -m "docs: refresh advisory backtest evidence"
```

---

## Merge Threshold

The PR is ready for final merge only when:

- `ADD` precision has improved enough to be defensible
- `REDUCE` has enough sample support to be meaningful
- confidence buckets correlate with actual outcomes
- the report is complete, stable, and sample-aware
- the sandboxed Docker suite passes

