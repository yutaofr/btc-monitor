import pandas as pd
from typing import Dict, Any
from src.indicators.base import IndicatorResult

class Hash_Ribbon:
    """
    Miner-recovery factor calculating Hash Ribbon state.
    Bullish when 30d SMA of hashrate crosses above 60d SMA (Recovery).
    Bearish when 30d SMA of hashrate crosses below 60d SMA (Capitulation).
    """
    def __init__(self):
        self.name = "Hash_Ribbon"

    def evaluate(self, df: pd.DataFrame) -> IndicatorResult:
        if df.empty or "hashrate" not in df.columns or len(df) < 2:
            return IndicatorResult(name=self.name, score=0.0, is_valid=False, details={}, weight=1.0)
            
        short_sma = df["hashrate"].rolling(window=30, min_periods=1).mean()
        long_sma = df["hashrate"].rolling(window=60, min_periods=1).mean()
        
        latest_short = short_sma.iloc[-1]
        latest_long = long_sma.iloc[-1]
        
        if pd.isna(latest_short) or pd.isna(latest_long):
            return IndicatorResult(name=self.name, score=0.0, is_valid=False, details={}, weight=1.0)
            
        if latest_short > latest_long:
            state = "Recovery"
            score = 8.0
        else:
            state = "Capitulation"
            score = -8.0
            
        details = {
            "state": state,
            "short_sma": float(latest_short),
            "long_sma": float(latest_long)
        }
        
        return IndicatorResult(name=self.name, score=score, is_valid=True, details=details, weight=1.0)
