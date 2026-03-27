import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone
from src.strategy.tadr_engine import TADREngine
from src.strategy.factor_models import FactorObservation
from src.monitoring.correlation_engine import CorrelationContext
from src.backtest.advisory_history import (
    _load_btc_daily, _to_weekly_ohlcv, calculate_rsi,
    _load_macro_series, _prepare_valuation_series, _prepare_fng_series,
    _score_technical, _score_macro, _score_valuation
)

def run_v3_acceptance_backtest():
    print("🚀 [V3 ACCEPTANCE] Starting TADREngine Historical Audit...")

    # 1. Load Data (Ensuring consistency with V2 backtest source)
    daily_df, source = _load_btc_daily()
    if daily_df is None or daily_df.empty:
        print("❌ Error: BTC Data Missing")
        return

    weekly = _to_weekly_ohlcv(daily_df)
    rsi_weekly = calculate_rsi(weekly["close"], period=14)
    net_liq, yields, dxy = _load_macro_series(weekly.index)
    m_cap_df, puell_df, hash_df = _prepare_valuation_series(weekly.index)
    fng_weekly = _prepare_fng_series(weekly.index)

    # 2. Initialize V3 Engine
    engine = TADREngine()
    records = []

    # Audit milestones (Bear markets / Halving years)
    audit_dates = ["2018-12-16", "2021-05-23", "2022-11-20", "2024-01-07"]

    print(f"📊 Analyzing {len(weekly)} weeks...")

    for idx in range(len(weekly)):
        timestamp = weekly.index[idx]

        # Aggregate observations (Mimicking live data provider)
        results = _score_technical(weekly, rsi_weekly, idx)
        results.extend(_score_macro(net_liq, yields, dxy, idx))
        results.extend(_score_valuation(m_cap_df, puell_df, hash_df, weekly, idx))

        # results.extend(_score_sentiment(fng_weekly, idx)) # Optional if data is sparse
        
        observations = []
        for res in results:
            observations.append(FactorObservation(
                name=res.name, score=res.score, is_valid=res.is_valid,
                details=res.details, description="", timestamp=timestamp,
                freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
            ))
            
        # Mock Correlation Context (Simulating dynamic weighting environment)
        # In real V3, this would come from CorrelationEngine
        ctx = CorrelationContext(
            correlations={"Net_Liquidity": 0.5 if idx > 50 else 0.0}, 
            regime_labels=["Audit_Mode"], is_valid=True
        )
        
        # 3. RUN V3 ENGINE
        rec = engine.evaluate(observations, context=ctx)
        state = engine.last_internal_state
        
        records.append({
            "timestamp": timestamp,
            "price": weekly["close"].iloc[idx],
            "action": rec.action,
            "target": state.target_allocation,
            "confidence": state.confidence,
            "score": state.strategic_score,
            "is_blocked": state.is_circuit_breaker_active
        })
        
        # 4. Immediate Audit for Milestones
        ts_str = timestamp.strftime("%Y-%m-%d")
        if ts_str in audit_dates:
            print(f"📍 [AUDIT] {ts_str} | Price: ${weekly['close'].iloc[idx]:.0f} | Action: {rec.action} | Target: {state.target_allocation:.1%} | Conf: {state.confidence*100:.1f}%")

    # 5. Summary Analysis
    df = pd.DataFrame(records)
    print("\n📈 [V3 SUMMARY METRICS]")
    print(f"Avg Target Allocation: {df['target'].mean():.1%}")
    print(f"Max Drawdown Avoidance (Target < 20% count): {len(df[df['target'] < 0.2])}")
    print(f"Bullish Conviction (Target > 80% count): {len(df[df['target'] > 0.8])}")
    print(f"Circuit Breaker Hits: {df['is_blocked'].sum()}")
    
    os.makedirs("data/acceptance", exist_ok=True)
    df.to_csv("data/acceptance/v3_tadr_audit_results.csv", index=False)
    print("✅ Audit Complete. Results saved to data/acceptance/v3_tadr_audit_results.csv")

if __name__ == "__main__":
    run_v3_acceptance_backtest()
