import pandas as pd
from typing import Dict, List, Optional

def calculate_forward_returns(prices: pd.Series, eval_date: pd.Timestamp, forward_days: List[int]) -> Dict[str, float]:
    """
    Given a series of prices and an evaluation date, calculate the percentage
    returns for a set of future forward periods.
    """
    returns = {}
    
    if eval_date not in prices.index:
        return returns
        
    base_price = prices[eval_date]
    if pd.isna(base_price) or base_price <= 0:
        return returns
        
    for days in forward_days:
        target_date = eval_date + pd.Timedelta(days=days)
        # Find closest date if target falls on weekend/missing
        future_prices = prices[prices.index >= target_date]
        if not future_prices.empty:
            future_price = future_prices.iloc[0]
            if not pd.isna(future_price):
                ret = ((future_price - base_price) / base_price) * 100
                returns[f"{days}_day_return"] = ret
                
    return returns

def evaluate_precision(action: str, forward_return: float) -> Optional[bool]:
    """
    Determines if an action was successful based on the forward return window.
    ADD requires a strictly positive return.
    REDUCE requires a strictly negative return.
    """
    if action in ["ADD", "BUY_NOW"]:
        return forward_return > 0
    elif action == "REDUCE":
        return forward_return < 0
    return None

def calculate_benchmark_dca_return(prices: pd.Series, start_date: pd.Timestamp, forward_days: int) -> Optional[float]:
    """
    Calculates the relative performance of a lump-sum buy at start_date 
    vs a daily time-uniform DCA over the next forward_days.
    Returns: (LumpSumOutcome / DCAOutcome) - 1.0 (as percentage)
    """
    if start_date not in prices.index:
        return None
        
    end_date = start_date + pd.Timedelta(days=forward_days)
    relevant_prices = prices[(prices.index >= start_date) & (prices.index <= end_date)]
    if relevant_prices.empty:
        return None
        
    lump_sum_price = prices[start_date]
    if lump_sum_price <= 0:
        return None
        
    # DCA Outcome: 1 / Average Price over the period
    avg_dca_price = relevant_prices.mean()
    if avg_dca_price <= 0:
        return None
        
    # Relative performance: (1/P_lump) / (1/P_dca) - 1 = P_dca / P_lump - 1
    # If P_dca > P_lump, lump sum was better (positive relative return)
    rel_perf = (avg_dca_price / lump_sum_price - 1.0) * 100
    return rel_perf
