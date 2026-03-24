# BTC Monitor Dual-Decision Implementation Plan

> **For Claude Code:** REQUIRED DEVELOPMENT MODE: use strict `test-driven-development`, `subagent-driven-development`, and `verification-before-completion` for every task in this plan. No task is complete without a failing test first, a passing regression test last, and fresh verification evidence.

**Goal:** Implement the dual-decision advisory architecture defined in `docs/2026-03-24-btc-monitor-dual-decision-add.md` and satisfy the requirements in `docs/2026-03-24-btc-monitor-dual-decision-srd.md`.

**Tech Stack:** Python 3.12, pandas, pytest, Docker, existing BTC indicator/fetcher stack

---

## Delivery Rules

### Rule 1: Strict TDD

Every task must follow:

1. write the failing test
2. run it and confirm the expected failure
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

## Epic 1: Split the Decision Domain

### User Story 1.1

As a maintainer, I want position advice and cash-entry advice to use different action vocabularies so that the system does not conflate rebalancing with new deployment.

Acceptance criteria:

- position advisory outputs only `ADD`, `REDUCE`, `HOLD`, `INSUFFICIENT_DATA`
- cash advisory outputs only `BUY_NOW`, `STAGGER_BUY`, `WAIT`, `INSUFFICIENT_DATA`
- action vocabularies are tested and non-overlapping

Strict tests:

- action vocabulary unit tests
- branch-separation regression tests

Tasks:

- define separate action enums or branch-specific outputs
- add tests that fail if one branch emits the other branch's action labels
- wire the outputs into branch-specific recommendation objects

### User Story 1.2

As a maintainer, I want a shared factor context so that both branches consume the same evidence substrate without duplicating policy.

Acceptance criteria:

- shared factor registry exists
- shared observation model exists
- both branches read the same factor metadata

Strict tests:

- registry completeness tests
- observation model tests
- parity tests across both branches

Tasks:

- introduce shared decision context objects
- keep factor registry as single source of truth
- add parity tests for registry usage

---

## Epic 2: Position Advisory

### User Story 2.1

As a user, I want a strict position adjustment engine so that `ADD` and `REDUCE` are only emitted on credible evidence.

Acceptance criteria:

- weak bullish evidence cannot trigger `ADD`
- weak overheated evidence cannot trigger `REDUCE`
- missing strategic evidence returns `INSUFFICIENT_DATA`

Strict tests:

- bullish false-positive regression tests
- overheated false-positive regression tests
- missing-block tests

Tasks:

- refactor the current advisory engine into a position advisory module
- tighten gate logic
- keep tactical confirmation explicit

### User Story 2.2

As a reviewer, I want confidence to be branch-specific so that position confidence does not masquerade as entry timing confidence.

Acceptance criteria:

- confidence is not shared across branches
- confidence is deterministic
- low-quality evidence cannot produce high confidence

Strict tests:

- confidence monotonicity tests
- branch-independence tests
- deterministic confidence tests

Tasks:

- implement separate confidence calibration inputs
- write monotonicity tests first
- calibrate by branch-specific buckets

---

## Epic 3: Incremental Cash Advisory

### User Story 3.1

As a user, I want a new-cash entry engine so that I can decide when to deploy fresh capital.

Acceptance criteria:

- `BUY_NOW`, `STAGGER_BUY`, `WAIT`, and `INSUFFICIENT_DATA` are supported
- the engine can return `WAIT` even when position advisory would say `HOLD`
- the branch is benchmark-aware

Strict tests:

- cash-entry action tests
- benchmark-vs-now comparison tests
- wait-vs-buy separation tests

Tasks:

- create `src/strategy/incremental_buy_engine.py`
- define entry-specific rules
- add tests for benchmark-aware timing outcomes

### User Story 3.2

As a user, I want the cash branch to be conservative about overpaying so that `BUY_NOW` is reserved for genuinely favorable windows.

Acceptance criteria:

- overheated market conditions veto `BUY_NOW`
- favorable long-horizon regimes may return `STAGGER_BUY`
- entry labels are not just forward-return direction checks

Strict tests:

- overheated veto tests
- stagger-buy tests
- benchmark-relative outcome tests

Tasks:

- add branch-specific tactical checks
- add price-stretch or valuation-depth inputs
- ensure `WAIT` remains reachable

---

## Epic 4: Backtesting and Calibration

### User Story 4.1

As a reviewer, I want separate backtests for position advice and cash-entry advice so that the two branches can be judged correctly.

Acceptance criteria:

- two separate backtest artifacts exist
- each branch has its own report and metrics
- sample counts are explicit for every action

Strict tests:

- artifact schema tests
- report format tests
- branch-specific backtest regression tests

Tasks:

- keep `advisory_backtest.py` for position advice
- add `incremental_buy_backtest.py`
- generate separate CSV and markdown reports

### User Story 4.2

As a reviewer, I want benchmark-aware cash metrics so that `BUY_NOW` can be compared against simple deployment rules.

Acceptance criteria:

- cash branch reports improvement over immediate buy benchmark
- cash branch reports improvement over staged DCA benchmark
- weak buckets are labeled honestly

Strict tests:

- benchmark comparison tests
- timing-edge tests
- inadequate-sample tests

Tasks:

- add benchmark calculators
- compute relative entry quality
- report regret and adverse excursion

### User Story 4.3

As a maintainer, I want confidence calibration to be branch-specific and sample-aware so that the output number is meaningful.

Acceptance criteria:

- confidence buckets are calibrated separately per branch
- buckets with low samples are labeled as such
- confidence does not saturate trivially

Strict tests:

- calibration bucket tests
- zero-count row tests
- monotonic confidence tests

Tasks:

- create calibration helpers
- keep bucket matrices complete
- preserve sample-aware reporting

---

## Epic 5: Final Verification

### User Story 5.1

As a reviewer, I want a fresh sandboxed verification run so that the final state is evidence-based.

Acceptance criteria:

- canonical Docker unit suite passes
- both branch reports regenerate successfully
- merge caveats remain honest about sample size

Strict tests:

- sandboxed unit suite
- backtest regeneration run
- report schema checks

Tasks:

- run Docker verification before completion
- regenerate committed artifacts
- update docs if metrics change materially

---

## Merge Threshold

The PR is ready for merge only when:

- both branches are implemented and tested
- both branches have separate backtests
- sample-aware confidence is honest
- benchmark-aware cash timing is present
- the sandboxed Docker suite passes

