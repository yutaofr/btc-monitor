# [COMPLETED] Plan: BTC Valuation Resonance Indicators (V3.0 TADR Alignment)

## Objective
Implement and integrate fundamental on-chain valuation indicators into the V3.0 TADR Framework. These indicators provide the "Fair Price" anchor for Strategic Evidence Blocks.

## Key Files & Context
- `src/fetchers/blockchain_fetcher.py`: Fetcher for Blockchain.info and Mempool.space JSON charts.
- `src/indicators/valuation.py`: Indicator class implementing MVRV_Proxy, Puell Multiple, and Hash Ribbon.
- `src/strategy/tadr_engine.py`: Primary V3.0 Integration point.
- `src/strategy/factor_registry.py`: Defines the gating and weighting policies for these indicators.

## Architecture Status (V3.0)

### 1. Data Layer (BlockchainFetcher)
- **Status**: Operational.
- **Endpoints**: MVRV, Miners-Revenue, Hash-Rate.
- **Resilience**: Integrated with `LiveDataProvider` for synchronization with Macro assets.

### 2. Indicator Logic (ValuationIndicator)
- **MVRV_Proxy**:
    - Normalized score based on historical percentiles.
    - High确信度因子 (Is_Critical=True).
- **Puell Multiple**:
    - Captures miner revenue cycles.
    - Essential for Bullish Accumulation regime detection.

### 3. TADR Integration
- **Strategic Block**: Valuation factors are aggregated into the `valuation` evidence block.
- **Dynamic Weighting**: Weight adjusts based on correlation context provided by `CorrelationEngine`.
- **Fail-Closed**: If MVRV or Puell data is stale (>72h), the system triggers `SYSTEM_GATE_LOCKED`.

## Verification
- **Unit Tests**: `tests/unit/indicators/test_valuation_indicators.py`.
- **Shadow Parity**: Verified via `tests/parity/shadow_parity_100_samples.py`.
- **Black-box**: 100% pass in "Bullish Accumulation" scenarios.

---
*Note: This track is officially merged into V3.0 Release Branch.*
