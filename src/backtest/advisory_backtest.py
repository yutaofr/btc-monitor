import pandas as pd
from src.backtest.metrics import calculate_forward_returns, evaluate_precision

def evaluate_history() -> pd.DataFrame:
    """Mock stub to be replaced or patched. Usually runs AdvisoryEngine over history."""
    return pd.DataFrame()

def fetch_prices() -> pd.Series:
    """Mock stub to be replaced or patched."""
    return pd.Series(dtype=float)

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
        
    precision_metrics = {}
    confidence_buckets = {}
    
    return {
        "precision_metrics": precision_metrics,
        "confidence_buckets": confidence_buckets,
        "metrics_df": metrics_df
    }

if __name__ == "__main__":
    generate_advisory_backtest()
