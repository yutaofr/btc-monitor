import pandas as pd
import numpy as np
import os
import requests
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation
from src.strategy.factor_registry import get_factor
from src.strategy.factor_utils import check_freshness
from src.backtest.metrics import calculate_forward_returns, evaluate_precision
from src.backtest.advisory_history import (
    IndicatorResult, _to_weekly_ohlcv, calculate_rsi, 
    _load_macro_series, _prepare_valuation_series, _load_btc_daily,
    _score_technical, _score_macro, _score_valuation,
    _prepare_fng_series
)

def generate_advisory_backtest(output_dir="data/backtest"):
    """Main entry point for authentic historical advisory validation."""
    print("Loading authentic daily price data from Binance...")
    daily_df, source = _load_btc_daily()
    if daily_df is None or daily_df.empty:
        print("[ERROR] No authentic BTC data available. Cannot proceed without real data.")
        return
    
    weekly = _to_weekly_ohlcv(daily_df)
    print(f"History Depth: {len(weekly)} weeks (Source: {source})")
    
    # Pre-calculate indicators on the full series
    rsi_weekly = calculate_rsi(weekly["close"], period=14)
    net_liq, yields, dxy = _load_macro_series(weekly.index)
    mvrv_weekly, puell_weekly, hash_weekly = _prepare_valuation_series(weekly.index)
    fng_weekly = _prepare_fng_series(weekly.index)
    
    engine = AdvisoryEngine()
    records = []
    
    print("Evaluating historical simulation via stateless engine (REAL DATA)...")
    for idx in range(len(weekly)):
        timestamp = weekly.index[idx]
        
        # 1. Technical Indicators (200WMA, RSI)
        results = _score_technical(weekly, rsi_weekly, idx)
        
        # 2. Macro Indicators (Net Liquidity, Yields, DXY)
        results.extend(_score_macro(net_liq, yields, dxy, idx))
        
        # 3. Valuation Indicators (MVRV, Puell, Hash Ribbon)
        results.extend(_score_valuation(mvrv_weekly, puell_weekly, hash_weekly, weekly, idx))
        
        # 4. Sentiment (FearGreed, CyclePosition)
        # FearGreed from fng_weekly
        fng_val = fng_weekly.iloc[idx] if fng_weekly is not None and idx < len(fng_weekly) else np.nan
        if pd.isna(fng_val):
            results.append(IndicatorResult("FearGreed", 0.0, is_valid=False, details={"reason": "Data unavailable"}))
        else:
            # Map [0, 100] to [+10, -10]
            fng_score = (50 - fng_val) / 5.0
            results.append(IndicatorResult("FearGreed", round(fng_score, 2), details={"value": fng_val}))
            
        # Cycle Position (Weekly close vs ATH)
        ath_so_far = weekly["high"].iloc[:idx+1].max()
        curr_p = weekly["close"].iloc[idx]
        drawdown = (curr_p - ath_so_far) / ath_so_far
        if drawdown < -0.7: cp_score = 10.0
        elif drawdown > -0.1: cp_score = -10.0
        else: cp_score = ((-drawdown - 0.4) / 0.3) * 10
        results.append(IndicatorResult("Cycle_Pos", round(cp_score, 2), details={"drawdown": drawdown}))

        # Pack into observations for the stateless engine
        observations = []
        for res in results:
            try:
                definition = get_factor(res.name)
                obs = FactorObservation(
                    name=res.name,
                    score=res.score,
                    is_valid=res.is_valid,
                    details=res.details or {},
                    description=f"Authentic {res.name} evaluation",
                    timestamp=timestamp,
                    freshness_ok=True,
                    confidence_penalty=0.0 if res.is_valid else 10.0,
                    blocked_reason=""
                )
                observations.append(obs)
            except KeyError:
                continue

        rec = engine.evaluate(observations)
        
        records.append({
            "timestamp": timestamp,
            "action": rec.action,
            "strategic_regime": rec.strategic_regime,
            "confidence": rec.confidence,
            "weekly_open": weekly["open"].iloc[idx],
            "weekly_close": weekly["close"].iloc[idx],
            "blocked_reasons": "; ".join(rec.blocked_reasons),
            "missing_factors": "; ".join(rec.missing_required_factors)
        })

    # Save to CSV
    df = pd.DataFrame(records)
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "advisory_backtest_result.csv")
    df.to_csv(csv_path, index=False)
    
    # Generate report
    report_path = os.path.join(output_dir, "advisory_performance_report.md")
    _generate_performance_report(df, daily_df["close"], report_path)
    print(f"Backtest completed. Report saved to data/backtest/advisory_performance_report.md")

def _generate_performance_report(df, full_prices, report_path):
    """Generate the markdown performance report from REAL results."""
    # Add forward returns for multiple horizons (28, 84, 182 days)
    results_list = []
    forward_windows = [28, 84, 182]
    
    for _, row in df.iterrows():
        eval_date = row["timestamp"]
        returns = calculate_forward_returns(full_prices, eval_date, forward_days=forward_windows)
        row_dict = row.to_dict()
        row_dict.update(returns)
        
        # Calculate precision for ADD/REDUCE across all windows
        for win in forward_windows:
            col = f"{win}_day_return"
            if row["action"] in ["ADD", "REDUCE"]:
                fwd_ret = returns.get(col)
                if fwd_ret is not None:
                    row_dict[f"precision_{win}"] = evaluate_precision(row["action"], fwd_ret)
        
        results_list.append(row_dict)
        
    metrics_df = pd.DataFrame(results_list)
    
    with open(report_path, "w") as f:
        f.write("# High-Confidence Advisory Performance Report\n")
        f.write(f"**Generated:** {pd.Timestamp.now()}\n")
        f.write(f"**History Length:** {len(df)} weeks\n\n")
        
        f.write("## 1. Action Distribution\n")
        dist = metrics_df["action"].value_counts(normalize=True).to_dict()
        f.write("| Action | Frequency | Count |\n|--------|-----------|-------|\n")
        counts = metrics_df["action"].value_counts().to_dict()
        for act in ["ADD", "REDUCE", "HOLD", "INSUFFICIENT_DATA"]:
            freq = dist.get(act, 0)
            count = counts.get(act, 0)
            f.write(f"| {act} | {freq:.2%} | {count} |\n")
        f.write("\n")
        
        f.write("## 2. Multi-Horizon Precision\n")
        f.write("| Action | 28d Precision | 84d Precision | 182d Precision |\n")
        f.write("|--------|---------------|---------------|----------------|\n")
        for action in ["ADD", "REDUCE"]:
            subset = metrics_df[metrics_df["action"] == action]
            p28 = subset["precision_28"].mean() if "precision_28" in subset.columns else 0
            p84 = subset["precision_84"].mean() if "precision_84" in subset.columns else 0
            p182 = subset["precision_182"].mean() if "precision_182" in subset.columns else 0
            f.write(f"| {action} | {p28:.1%} | {p84:.1%} | {p182:.1%} |\n")
        f.write("\n")
        
        f.write("## 3. Regime Breakdown\n")
        f.write("| Regime | Count | Avg Confidence | Conf Std |\n|--------|-------|----------------|----------|\n")
        if "strategic_regime" in metrics_df.columns:
            regimes = metrics_df.groupby("strategic_regime")
            for name, group in regimes:
                f.write(f"| {name} | {len(group)} | {group['confidence'].mean():.1f} | {group['confidence'].std():.1f} |\n")

        f.write("\n## 4. False Positive Analysis\n")
        f.write("| Action | Horizon | FP Count | Sample |\n")
        f.write("|--------|---------|----------|--------|\n")
        for action in ["ADD", "REDUCE"]:
            for win in [28, 84, 182]:
                col = f"precision_{win}"
                if col in metrics_df.columns:
                    fp_subset = metrics_df[(metrics_df["action"] == action) & (metrics_df[col] == 0)]
                    count = len(fp_subset)
                    sample = fp_subset["timestamp"].min() if not fp_subset.empty else "None"
                    f.write(f"| {action} | {win}d | {count} | {sample} |\n")
            
    return metrics_df

if __name__ == "__main__":
    generate_advisory_backtest()
