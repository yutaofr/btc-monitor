import pandas as pd
from src.backtest.metrics import calculate_forward_returns, evaluate_precision

from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation
from src.backtest.btc_backtest import (
    _load_btc_daily, _to_weekly_ohlcv, calculate_rsi, 
    _load_macro_series, _prepare_valuation_series, 
    _score_technical, _score_macro, _score_valuation, _score_missing
)

def fetch_prices() -> pd.Series:
    daily, _ = _load_btc_daily()
    return daily["close"]

def evaluate_history() -> pd.DataFrame:
    """Runs AdvisoryEngine over history."""
    daily, _ = _load_btc_daily()
    weekly = _to_weekly_ohlcv(daily)
    
    daily_close = daily["close"]
    pi_daily = pd.DataFrame({
        "sma111": daily_close.rolling(window=111).mean(),
        "sma350x2": daily_close.rolling(window=350).mean() * 2
    })
    pi_weekly = pi_daily.resample("W-FRI").last().reindex(weekly.index).ffill()
    rsi_weekly = calculate_rsi(weekly["close"])

    net_liq, yields = _load_macro_series()
    if net_liq is not None:
        net_liq = net_liq.reindex(weekly.index).ffill()
    if yields is not None:
        yields = yields.reindex(weekly.index).ffill()

    mvrv_weekly, puell_weekly = _prepare_valuation_series(weekly.index)
    
    engine = AdvisoryEngine()
    records = []

    for idx, timestamp in enumerate(weekly.index):
        results = []
        results.extend(_score_technical(weekly, pi_weekly, rsi_weekly, idx))
        results.extend(_score_macro(net_liq, yields, idx))
        results.extend(_score_valuation(mvrv_weekly, puell_weekly, idx))
        results.append(_score_missing("FearGreed", "Historical FNG unavailable"))
        results.append(_score_missing("Options_Wall", "Historical options unavailable"))
        results.append(_score_missing("ETF_Flow", "Historical ETF flow unavailable"))
        
        from src.strategy.factor_registry import get_factor
        from src.strategy.factor_utils import check_freshness
        
        observations = []
        for res in results:
            try:
                definition = get_factor(res.name)
                # In backtest, we check freshness relative to the current loop timestamp
                obs_ts = res.timestamp if res.timestamp is not None else timestamp
                is_fresh = check_freshness(obs_ts, definition.freshness_ttl_hours, current_time=timestamp)
            except KeyError:
                is_fresh = True
                obs_ts = res.timestamp if res.timestamp is not None else timestamp

            observations.append(
                FactorObservation(
                    name=res.name,
                    score=res.score,
                    is_valid=res.is_valid,
                    confidence_penalty=10 if not res.is_valid else 0,
                    details=getattr(res, "details", {}),
                    description=getattr(res, "description", ""),
                    timestamp=obs_ts,
                    freshness_ok=is_fresh,
                    blocked_reason=""
                )
            )
        
        rec = engine.evaluate(observations)
        
        records.append({
            "date": timestamp,
            "action": rec.action,
            "confidence": rec.confidence,
            "tactical_state": rec.tactical_state,
            "strategic_regime": rec.strategic_regime,
            "score": float(rec.confidence), # Mock equivalent for historical parity
            "weekly_open": weekly["open"].iloc[idx],
            "weekly_close": weekly["close"].iloc[idx]
        })

    return pd.DataFrame(records)


import os

def generate_advisory_backtest() -> dict:
    """
    Generates the advisory backtest data. 
    Outputs forward 4-week, 12-week, and 26-week action-bucket metrics.
    """
    history_df = evaluate_history()
    prices = fetch_prices()
    
    if history_df.empty:
        return {"precision_metrics": {}, "confidence_buckets": {}, "metrics_df": pd.DataFrame()}
        
    history_df["date"] = pd.to_datetime(history_df["date"])
    
    forward_windows = [28, 84, 182] # 4wk, 12wk, 26wk in days
    
    metrics_list = []
    
    for _, row in history_df.iterrows():
        action = row.get("action", "HOLD")
        confidence = row.get("confidence", 0)
        eval_date = row["date"]
        
        returns = calculate_forward_returns(prices, eval_date, forward_days=forward_windows)
        
        row_metrics = row.to_dict()
        row_metrics.update(returns)
        
        # Calculate precision based on the shortest forward window for simplicity in the schema
        # In reality, might calculate Precision per window
        if "28_day_return" in returns:
            row_metrics["precision"] = evaluate_precision(action, returns["28_day_return"])
        else:
            row_metrics["precision"] = None
            
        metrics_list.append(row_metrics)
        
    metrics_df = pd.DataFrame(metrics_list)
    
    # Ensure columns exist even if empty
    for w in forward_windows:
        col = f"{w}_day_return"
        if col not in metrics_df.columns:
            metrics_df[col] = pd.NA
            
    if "precision" not in metrics_df.columns:
        metrics_df["precision"] = pd.NA
        
    # Calculate aggregate summaries
    precision_metrics = {}
    for action in ["ADD", "REDUCE"]:
        subset = metrics_df[metrics_df["action"] == action]
        if not subset.empty:
            total = len(subset.dropna(subset=["precision"]))
            correct = len(subset[subset["precision"] == True])
            precision_metrics[action] = {
                "count": total,
                "precision": round(correct / total, 4) if total > 0 else 0.0
            }

    # Confidence distribution (Bucketing)
    def bucket_confidence(c):
        if c < 40: return "<40 (Low)"
        if c < 60: return "40-60 (Mixed)"
        if c < 80: return "60-80 (Emerging)"
        return "80-100 (Strong)"

    metrics_df["conf_bucket"] = metrics_df["confidence"].apply(bucket_confidence)
    confidence_buckets = metrics_df.groupby(["conf_bucket", "action"]).size().unstack(fill_value=0).to_dict()

    # Persist the generated artifact
    output_dir = "data/backtest"
    os.makedirs(output_dir, exist_ok=True)
    metrics_df.to_csv(os.path.join(output_dir, "advisory_backtest_result.csv"), index=False)
    print(f"Advisory backtest generated ({len(metrics_df)} weeks of history). Artifact saved to {output_dir}/advisory_backtest_result.csv.")
    print(f"Precision Summary: {precision_metrics}")
    
    return {
        "precision_metrics": precision_metrics,
        "confidence_buckets": confidence_buckets,
        "metrics_df": metrics_df
    }


if __name__ == "__main__":
    generate_advisory_backtest()
