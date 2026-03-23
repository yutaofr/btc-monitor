import pytest
import pandas as pd
from datetime import datetime
from src.indicators.miner_cycle import Hash_Ribbon

def test_hash_ribbon_bullish_recovery():
    # Simulate Hash Ribbon recovery: 30d moving average crosses above 60d moving average
    # after a period of being below (capitulation).
    dates = pd.date_range(end=datetime.now(), periods=65, freq="D")
    base_data = [80] * 35 + [85, 90, 85, 80, 95] * 6 # Pad to past 60 to allow crossing
    df = pd.DataFrame({"hashrate": base_data}, index=dates)
    
    indicator = Hash_Ribbon()
    result = indicator.evaluate(df)
    
    assert result.is_valid
    assert result.score > 0.0 # Bullish score
    assert "recovery" in result.details.get("state", "").lower()

def test_hash_ribbon_capitulation_bearish():
    # Simulate Hash Ribbon capitulation: 30d crosses below 60d
    dates = pd.date_range(end=datetime.now(), periods=65, freq="D")
    base_data = [120] * 35 + [115, 110, 105, 95, 80] * 6 # Pad to past 60 to allow crossing
    df = pd.DataFrame({"hashrate": base_data}, index=dates)
    
    indicator = Hash_Ribbon()
    result = indicator.evaluate(df)
    
    assert result.is_valid
    assert result.score < 0.0 # Bearish score
    assert "capitulation" in result.details.get("state", "").lower()

def test_hash_ribbon_invalid_data():
    indicator = Hash_Ribbon()
    result = indicator.evaluate(pd.DataFrame())
    assert not result.is_valid
