import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.backtest.metrics import calculate_forward_returns, evaluate_precision

def test_calculate_forward_returns():
    # Mock price history
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    prices = pd.Series([100.0 + i for i in range(30)], index=dates)
    
    # We evaluate at day 0
    eval_date = dates[0]
    
    returns = calculate_forward_returns(prices, eval_date, forward_days=[7, 14])
    
    assert "7_day_return" in returns
    assert "14_day_return" in returns
    assert round(returns["7_day_return"], 2) == 7.0 # (107-100)/100
    assert round(returns["14_day_return"], 2) == 14.0 # (114-100)/100

def test_evaluate_precision():
    # If action is ADD, precision is positive if forward returns are positive
    assert evaluate_precision("ADD", 5.0) == True
    assert evaluate_precision("ADD", -5.0) == False
    
    # If action is REDUCE, precision is positive if forward returns are negative
    assert evaluate_precision("REDUCE", -5.0) == True
    assert evaluate_precision("REDUCE", 5.0) == False
    
    # HOLD assumes neutral (None for strict precision metric)
    assert evaluate_precision("HOLD", 5.0) is None
