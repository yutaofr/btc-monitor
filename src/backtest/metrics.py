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
    if action == "ADD":
        return forward_return > 0
    elif action == "REDUCE":
        return forward_return < 0
    return None
