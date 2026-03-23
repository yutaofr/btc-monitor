import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.indicators.miner_cycle import calculate_hash_ribbon

def test_hash_ribbon_recovery():
    """
    Test recovery signal: 30d MA crosses ABOVE 60d MA.
    """
    # Create 90 days of synthetic hashrate
    dates = [datetime.now() - timedelta(days=i) for i in range(90)]
    dates.reverse()
    
    # Simulate a dip and recovery
    # Days 0-60: trending down
    # Days 61-90: trending up sharply
    hashrate = []
    for i in range(60):
        hashrate.append(100 - (i * 0.5))
    for i in range(30):
        hashrate.append(70 + (i * 2.0))
        
    df = pd.DataFrame({"value": hashrate}, index=dates)
    
    result = calculate_hash_ribbon(df)
    assert result.name == "Hash_Ribbon"
    assert result.is_valid is True
    # In recovery phase (30d > 60d), score should be BULLISH
    assert result.score >= 5.0

def test_hash_ribbon_capitulation():
    """
    Test capitulation signal: 30d MA crosses BELOW 60d MA.
    """
    dates = [datetime.now() - timedelta(days=i) for i in range(90)]
    dates.reverse()
    
    # Simulate a crash
    hashrate = []
    for i in range(60):
        hashrate.append(100)
    for i in range(30):
        hashrate.append(50) # Sharp drop
        
    df = pd.DataFrame({"value": hashrate}, index=dates)
    
    result = calculate_hash_ribbon(df)
    # In capitulation, score should be BEARISH or Neutral (waiting for recovery)
    # But often Hash_Ribbon is used primarily for the BUY signal when it un-crosses.
    # We'll expect a low score during capitulation.
    assert result.score <= 0.0
