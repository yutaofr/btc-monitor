# Plan: BTC Valuation Resonance Indicators (Free Data Sources)

## Objective
Implement a new "Valuation Resonance" module to provide a "fair price" assessment of Bitcoin using free, public data sources (Blockchain.info & Mempool.space). This will supplement the existing technical and sentiment indicators with fundamental on-chain data.

## Key Files & Context
- `src/fetchers/blockchain_fetcher.py`: New fetcher for Blockchain.info and Mempool.space JSON charts.
- `src/indicators/valuation.py`: New indicator class implementing MVRV, Puell Multiple, and Production Cost.
- `src/strategy/engine.py`: Integration point for the new indicators.

## Implementation Steps

### 1. Research & Fetching (BlockchainFetcher)
- **Blockchain.info Charts**: Use the direct JSON endpoints (no API key required):
    - `mvrv`: Market Value to Realized Value ratio.
    - `miners-revenue`: Daily total revenue in USD.
    - `realized-price`: Average price at which coins last moved.
    - `hash-rate`: Total network hashrate (EH/s).
- **Mempool.space**: Get difficulty and subsidy info.

### 2. Indicator Logic (ValuationIndicator)
- **MVRV Z-Score / Ratio**:
    - Score +10 when MVRV < 1.0 (Price is below network cost).
    - Score -10 when MVRV > 3.7 (Historical bubble peaks).
- **Puell Multiple**:
    - `Daily Revenue / 365d Moving Average of Daily Revenue`.
    - Score +10 when < 0.5 (Miner capitulation).
    - Score -10 when > 4.0 (Extreme miner profit).
- **Miner Production Cost (Production Cost Model)**:
    - Use `Price / Realized Price` or an estimated cost using Hashrate.
    - Score +10 when Price approaches the floor.

### 3. Strategy Engine Update
- Add `ValuationIndicator` to `StrategyEngine.__init__`.
- Append new scores in `evaluate()`.
- The weighted average naturally handles the new indicators.

## Verification & Testing
- **Unit Tests**:
    - `tests/unit/test_blockchain_fetcher.py`: Mock JSON responses for all endpoints.
    - `tests/unit/test_valuation_indicators.py`: Verify scoring logic with edge case data.
- **Dry-run**:
    - Run `python src/main.py --now` to see the new report format with Valuation scores.
