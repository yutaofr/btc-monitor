import pandas as pd
from datetime import datetime
from src.indicators.base import IndicatorResult

def calculate_hash_ribbon(hash_df: pd.DataFrame) -> IndicatorResult:
    """
    Miner-stress recovery signal using free hash-rate data.
    30d MA > 60d MA = Recovery (Bullish).
    30d MA < 60d MA = Capitulation (Bearish/Neutral).
    """
    if hash_df is None or hash_df.empty or len(hash_df) < 60:
        return IndicatorResult("Hash_Ribbon", 0.0, is_valid=False)

    # Clean and sort
    df = hash_df.sort_index()
    
    # Calculate MAs
    df['ma30'] = df['value'].rolling(window=30).mean()
    df['ma60'] = df['value'].rolling(window=60).mean()
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    ma30 = latest['ma30']
    ma60 = latest['ma60']
    
    if pd.isna(ma30) or pd.isna(ma60):
        return IndicatorResult("Hash_Ribbon", 0.0, is_valid=False)
        
    score = 0.0
    if ma30 > ma60:
        # Recovery phase
        # If it just crossed, it's a strong signal. 
        # For simplicity, we'll check if it was below ma60 recently
        score = 8.0 if latest['value'] > ma30 else 5.0
    else:
        # Capitulation phase
        score = -2.0
        
    return IndicatorResult(
        "Hash_Ribbon", 
        score, 
        is_valid=True,
        timestamp=latest.name,
        details={"ma30": round(ma30, 2), "ma60": round(ma60, 2)},
        description="30d MA above 60d MA indicates miner recovery." if score > 0 else "Miner capitulation in progress."
    )
