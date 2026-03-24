# BTC Monitor SRD: Dual-Decision BTC Advisory

> **For Claude Code:** This document is the source of truth for a BTC advisory system with two separate decision branches: position adjustment and incremental cash deployment. The system must stay advisory-only, stateless, reproducible, and free of execution state.

## Metadata

- Status: Draft
- Date: 2026-03-24
- Audience: Maintainers and Claude Code agents
- Scope: Requirements for a dual-decision BTC advisory system

## Problem Statement

The current system answers one question well enough for production use: whether to `ADD`, `REDUCE`, `HOLD`, or return `INSUFFICIENT_DATA` for an existing BTC position.

It does not yet answer a second, distinct question:

- if fresh capital is available today, is this a good BTC entry window?

These are different decision problems with different objectives, different labels, and different backtest targets. They must not be forced into one shared output space.

## Decision Split

### Branch 1: Position Advisory

This branch answers:

- should the current BTC exposure be increased
- should it be reduced
- should it be held
- is there enough evidence to decide

Required actions:

- `ADD`
- `REDUCE`
- `HOLD`
- `INSUFFICIENT_DATA`

### Branch 2: Incremental Cash Advisory

This branch answers:

- should new cash be deployed now
- should it be staggered
- should it wait for a better setup
- is there enough evidence to decide

Required actions:

- `BUY_NOW`
- `STAGGER_BUY`
- `WAIT`
- `INSUFFICIENT_DATA`

## Acceptance Decision

The system is **not complete** until both branches are implemented, independently validated, and sample-aware.

The system is acceptable only when:

- position advisory is statistically credible on its own
- incremental cash advisory has a measurable timing edge over a simple buy-now benchmark
- confidence is calibrated separately for each branch
- missing required evidence fails closed
- the two branches do not share labels or benchmarks

## Objective

Build a stateless BTC advisory system that:

- uses the same factor substrate
- emits two independent recommendations
- keeps execution state out of the core decision path
- keeps capital sizing out of the core decision path
- supports strict TDD and reproducible backtests

## Non-Goals

- no auto-trading
- no budget multiplier
- no monthly rollover or pacing
- no position sizing engine
- no paid data sources
- no exact top/bottom prediction

## First Principles

### Position Advisory

This branch is about marginal exposure management.

It should answer:

- is the long-term BTC regime favorable
- is the tactical setup aligned
- is risk expanding or contracting
- should the existing position be adjusted

### Incremental Cash Advisory

This branch is about opportunity cost.

It should answer:

- is it better to deploy cash now
- or wait for a materially better entry

This is a timing problem, not a position-management problem.

The correct benchmark is not the same as the position branch. It must compare against:

- immediate lump-sum buy
- staged DCA buy

## Success Criteria

The system is successful only if:

- the position branch achieves sample-aware `ADD` / `REDUCE` precision
- the cash branch beats at least one naïve deployment benchmark on a repeated historical basis
- confidence buckets correlate with historical success
- the report is honest about weak buckets and low sample sizes
- both branches remain easy to audit

## Required Outputs

### Position Advisory Output

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

### Incremental Cash Output

- `action`
- `confidence`
- `cash_entry_regime`
- `supporting_factors`
- `conflicting_factors`
- `missing_required_blocks`
- `missing_required_factors`
- `blocked_reasons`
- `freshness_warnings`
- `excluded_research_factors`
- `summary`
- `deployment_style`

## Required Evidence Blocks

### Position Advisory

- `valuation`
- `trend_cycle`
- `macro_liquidity`
- `sentiment_tactical`

### Incremental Cash Advisory

- `valuation`
- `trend_cycle`
- `macro_liquidity`
- `sentiment_tactical`
- optional `market_structure`

## Risk Policy

The system must fail closed when:

- a required strategic block is missing
- freshness is stale on required factors
- the branch-specific evidence is contradictory
- the branch-specific sample count is too small to support a real claim

## Statistical Policy

Both branches must be evaluated with:

- walk-forward validation
- horizon-specific precision
- sample counts per action
- confidence bucket analysis
- false positive and false negative analysis
- regime-level breakdown

For the cash branch, the primary metric is not directional precision alone. It is whether the recommended deployment timing improves realized entry quality versus benchmark deployment.

