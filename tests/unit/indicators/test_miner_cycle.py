import pytest
import pandas as pd
from datetime import datetime
from src.indicators.miner_cycle import Hash_Ribbon

def test_hash_ribbon_bullish_recovery():
    # Simulate Hash Ribbon recovery: 30d moving average crosses above 60d moving average
    # after a period of being below (capitulation).
    dates = pd.date_range(end=datetime.now(), periods=10, freq="D")
    data = {"hashrate": [80, 85, 90, 85, 80, 95, 105, 110, 115, 120]}
    df = pd.DataFrame(data, index=dates)
    
    indicator = Hash_Ribbon()
    result = indicator.evaluate(df)
    
    assert result.is_valid
    assert result.score > 0.0 # Bullish score
    assert "recovery" in result.details.get("state", "").lower()

def test_hash_ribbon_capitulation_bearish():
    # Simulate Hash Ribbon capitulation: 30d crosses below 60d
    dates = pd.date_range(end=datetime.now(), periods=10, freq="D")
    data = {"hashrate": [120, 115, 110, 105, 95, 80, 85, 90, 85, 80]}
    df = pd.DataFrame(data, index=dates)
    
    indicator = Hash_Ribbon()
    result = indicator.evaluate(df)
    
    assert result.is_valid
    assert result.score < 0.0 # Bearish score
    assert "capitulation" in result.details.get("state", "").lower()

def test_hash_ribbon_invalid_data():
    indicator = Hash_Ribbon()
    result = indicator.evaluate(pd.DataFrame())
    assert not result.is_valid
