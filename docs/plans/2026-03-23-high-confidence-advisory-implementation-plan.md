# BTC Monitor High-Confidence Advisory Implementation Plan

> **For Claude Code:** REQUIRED DEVELOPMENT MODE: use strict `test-driven-development`, `subagent-driven-development`, and `verification-before-completion` for this plan. No production code without a failing test first. No task is complete without spec review, code-quality review, and fresh verification evidence.

**Goal:** Implement the advisory-only architecture defined in `docs/2026-03-23-btc-monitor-high-confidence-advisory-add.md` and satisfy the requirements in `docs/2026-03-23-btc-monitor-high-confidence-advisory-srt.md`.

**Tech Stack:** Python 3.12, pandas, requests, ccxt, yfinance, fredapi, pytest

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

### Epic 1: Advisory Domain Foundation

Purpose: create the stateless advisory contract and remove policy drift.

### Epic 2: Advisory Decision Engines

Purpose: implement strategic regime logic, tactical confirmation, and advisory action gates.

### Epic 3: Factor Expansion and Policy Hardening

Purpose: add missing factors and enforce block-based policy.

### Epic 4: Reporting and Backtest Validation

Purpose: rebuild reporting and backtest around advisory quality.

### Epic 5: Documentation and Acceptance Alignment

Purpose: align repo docs, commands, and committed artifacts with the new architecture.

---

## Epic 1: Advisory Domain Foundation

### User Story 1.1

As a maintainer, I want a central factor registry so that strategy, reporting, and backtest all use one policy source.

Acceptance criteria:

- `factor_registry.py` exists
- all production and research-only factors are registered
- every registered factor has the metadata required by the SRT
- no duplicated factor-policy constants remain in active use

Strict tests:

- registry completeness test
- registry uniqueness test
- regression test proving production/backtest/reporting all read from the registry

Tasks:

- create `src/strategy/factor_models.py` with `FactorDefinition`, `FactorObservation`, and `Recommendation`
- create `src/strategy/factor_registry.py`
- port factor policy metadata out of `src/strategy/policies.py`
- add unit tests for registry completeness and uniqueness
- add parity tests that registry metadata is visible to strategy and backtest

### User Story 1.2

As a maintainer, I want a stateless advisory engine boundary so that recommendation logic no longer depends on execution state.

Acceptance criteria:

- advisory engine accepts only factor observations and policy inputs
- advisory engine does not import `StateTracker`
- advisory engine does not use budget or monthly execution fields

Strict tests:

- isolation tests for advisory engine constructor and call path
- import-boundary regression test
- deterministic recommendation test for identical inputs

Tasks:

- create `src/strategy/advisory_engine.py`
- define stateless engine interface
- add tests that fail if advisory code imports execution-state modules
- add deterministic fixture-based recommendation tests

---

## Epic 2: Advisory Decision Engines

### User Story 2.1

As a user, I want a strategic regime engine so that long-horizon conviction is computed from slow evidence only.

Acceptance criteria:

- strategic engine outputs only allowed regime states
- tactical factors cannot affect strategic regime
- missing required strategic evidence can return `INSUFFICIENT_DATA`

Strict tests:

- regime-state unit tests
- tactical-isolation tests
- missing-required-block tests

Tasks:

- refactor `src/strategy/strategic_engine.py` to use block-aware inputs
- define regime mapping rules from the ADD
- write regime tests first
- add missing-block regression tests

### User Story 2.2

As a user, I want a tactical confirmation engine so that short-horizon timing can refine but not override structural regime.

Acceptance criteria:

- tactical engine outputs only allowed tactical states
- tactical-only bullish inputs cannot create `ADD`
- tactical-only bearish inputs cannot create `REDUCE`

Strict tests:

- tactical-state unit tests
- tactical-only false-positive regression tests

Tasks:

- refactor `src/strategy/tactical_engine.py`
- add `Short_Term_Stretch` support to the tactical contract
- write failing tactical-state tests
- implement minimum logic to pass

### User Story 2.3

As a user, I want explicit `ADD`, `REDUCE`, `HOLD`, and `INSUFFICIENT_DATA` gates so that recommendations fail closed and are evidence-based.

Acceptance criteria:

- one-factor bullish scenario cannot return `ADD`
- one-factor overheated scenario cannot return `REDUCE`
- missing required blocks return `INSUFFICIENT_DATA`
- mixed but adequate evidence returns `HOLD`

Strict tests:

- positive `ADD` gate test
- blocked `ADD` gate test
- positive `REDUCE` gate test
- blocked `REDUCE` gate test
- one-factor false-positive regression tests for both directions
- `HOLD` versus `INSUFFICIENT_DATA` semantic tests

Tasks:

- implement action-gate logic in `src/strategy/advisory_engine.py`
- write gate tests before implementation
- add explicit blocked-reason fields
- add conflict-count and coverage-threshold logic

### User Story 2.4

As a user, I want confidence scoring tied to evidence quality so that strong and weak recommendations are clearly separated.

Acceptance criteria:

- confidence is deterministic
- low-quality evidence cannot produce high-confidence action
- recommendations below threshold are downgraded to `HOLD`, except for `INSUFFICIENT_DATA`

Strict tests:

- confidence monotonicity tests
- low-evidence downgrade tests
- deterministic confidence tests

Tasks:

- implement confidence scoring inputs from the ADD
- write monotonicity tests first
- implement downgrade behavior

---

## Epic 3: Factor Expansion and Policy Hardening

### User Story 3.1

As a user, I want a miner-recovery factor so that `ADD` can rely on more than price-location proxies.

Acceptance criteria:

- `Hash_Ribbon` or approved equivalent exists
- factor is replayable in backtest
- factor is registered with metadata and freshness rules

Strict tests:

- factor calculation unit tests
- backtest replay tests
- registry inclusion tests

Tasks:

- add `src/indicators/miner_cycle.py`
- implement `Hash_Ribbon`
- write fixture-based tests for normal, bullish-recovery, and invalid-data cases
- register the factor and wire it into strategy evaluation

### User Story 3.2

As a user, I want broader macro confirmation so that macro filtering does not rely only on net liquidity and nominal yields.

Acceptance criteria:

- `DXY_Regime` exists
- `Yields` is redefined as a regime factor, not only short-window delta
- both factors are replayable or explicitly blocked

Strict tests:

- macro regime tests
- missing-data fail-closed tests
- registry and backtest parity tests

Tasks:

- extend macro indicator module for `DXY_Regime`
- redesign `Yields` into regime logic
- write failing regime tests
- implement replay-compatible data flow

### User Story 3.3

As a maintainer, I want policy hardening for excluded factors so that research-only inputs cannot leak into production actions.

Acceptance criteria:

- `Pi_Cycle` is removed from active live evaluation or explicitly marked research-only
- research-only factors cannot affect action gates
- research-only factors remain reportable

Strict tests:

- action-isolation tests for research-only factors
- reporting tests for research-only visibility
- regression tests for `Pi_Cycle` treatment

Tasks:

- remove or reclassify `Pi_Cycle`
- harden research-only handling in advisory path
- add regression tests proving research-only factors do not change actions

---

## Epic 4: Reporting and Backtest Validation

### User Story 4.1

As a user, I want advisory reports that explain blocked and allowed decisions so that I can trust the recommendation semantics.

Acceptance criteria:

- report shows recommendation, confidence, regime, tactical state, supporting factors, conflicting factors, missing factors, missing blocks, freshness warnings, and excluded research factors
- report distinguishes `HOLD` from `INSUFFICIENT_DATA`

Strict tests:

- snapshot tests for representative reports
- unit tests for blocked-reason rendering

Tasks:

- refactor `src/strategy/reporting.py` to consume `Recommendation`
- write report snapshot tests first
- add explicit blocked-reason and missing-block sections

### User Story 4.2

As a maintainer, I want an advisory backtest so that validation measures recommendation quality rather than only portfolio PnL.

Acceptance criteria:

- advisory backtest outputs forward 4-week, 12-week, and 26-week action-bucket metrics
- precision and error metrics exist for `ADD` and `REDUCE`
- confidence-bucket monotonicity is reported
- cycle-sliced summary tables are produced

Strict tests:

- metric-calculation unit tests
- output-schema tests
- policy parity tests against live advisory logic

Tasks:

- create `src/backtest/advisory_backtest.py`
- create supporting `datasets.py` and `metrics.py` modules if needed
- write failing metric tests first
- implement advisory outputs and schema checks

### User Story 4.3

As a maintainer, I want backtest artifacts to match current code so that committed evidence is trustworthy.

Acceptance criteria:

- committed advisory backtest artifacts are generated from current code
- artifact schema matches current implementation
- stale legacy acceptance artifacts are removed or clearly deprecated

Strict tests:

- artifact schema tests
- regeneration command documented and verified

Tasks:

- define advisory backtest artifact schema
- add tests for schema and required columns
- regenerate artifacts after implementation stabilizes

---

## Epic 5: Documentation and Acceptance Alignment

### User Story 5.1

As a maintainer, I want repo documentation aligned with the advisory architecture so that docs do not promise behavior the code does not implement.

Acceptance criteria:

- `README.md` reflects advisory-only behavior
- stale threshold-driven descriptions are removed or clearly deprecated
- verification commands reflect the new advisory backtest entry point

Strict tests:

- doc consistency review checklist
- grep-based regression checks for stale behavior claims where practical

Tasks:

- update `README.md`
- update `GEMINI.md`
- update references to thresholds and execution semantics
- add a documentation review checklist to the final verification step

### User Story 5.2

As a tech lead, I want acceptance to be explicitly tied to SRT traceability so that no requirement ships without a corresponding test.

Acceptance criteria:

- each SRT functional requirement maps to implemented tests
- the final implementation report includes a traceability checklist

Strict tests:

- requirement-to-test review gate

Tasks:

- maintain a traceability checklist during implementation
- verify each SRT row has corresponding automated tests before sign-off

---

## Execution Order

Recommended order:

1. Story 1.1
2. Story 1.2
3. Story 2.1
4. Story 2.2
5. Story 2.3
6. Story 2.4
7. Story 3.1
8. Story 3.2
9. Story 3.3
10. Story 4.1
11. Story 4.2
12. Story 4.3
13. Story 5.1
14. Story 5.2

This ordering keeps policy and data contracts stable before factor expansion and backtest rebuild.

---

## Story-Level Verification Commands

Minimum commands for story completion:

```bash
docker compose run --rm tests
```

Additional gate for backtest and acceptance stories:

```bash
docker compose run --rm app python -m src.backtest.advisory_backtest
```

If the module path changes during implementation, update the plan and preserve the verification requirement.

---

## Final Release Checklist

- all stories completed in TDD mode
- all independent tasks executed in subagent-driven mode
- all SRT traceability rows covered by automated tests
- fresh verification commands run and recorded
- advisory backtest artifacts regenerated from current code
- docs aligned with implementation

## Deliverable

This plan is the implementation backlog for the advisory refactor. It is ready to be executed task by task under strict TDD and subagent-driven development.
