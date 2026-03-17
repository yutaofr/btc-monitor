import requests
import pandas as pd
from src.fetchers.binance_fetcher import BinanceFetcher
from src.indicators.base import IndicatorResult

class SentimentCycleIndicator:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or BinanceFetcher()
        self.fng_url = "https://api.alternative.me/fng/?limit=1"

    def get_fear_greed_score(self):
        """
        Fetch and score Fear & Greed Index.
        Extreme Fear (< 20) -> +10
        Extreme Greed (> 80) -> -10
        """
        try:
            response = requests.get(self.fng_url, timeout=10)
            data = response.json()
            val = int(data['data'][0]['value'])
            
            # Map [0, 100] to [+10, -10]
            # Neutral (50) -> 0
            score = (50 - val) / 5.0 # 50->0, 0->10, 100->-10
            
            return IndicatorResult(
                name="FearGreed",
                score=round(score, 2),
                details={"value": val},
                description=f"Fear & Greed Index is at {val} ({data['data'][0]['value_classification']})"
            )
        except Exception as e:
            print(f"[ERROR] Failed to fetch Fear & Greed: {e}")
            return IndicatorResult("FearGreed", 0, description="Fetch error")

    def get_cycle_position_score(self):
        """
        Estimate cycle position based on drawdown from ATH.
        Logic: Use confirmed weekly close vs historical high.
        """
        df = self.fetcher.fetch_ohlcv(timeframe="1w", limit=250) # ~5 years
        if df is None or len(df) < 50:
            return IndicatorResult("Cycle_Pos", 0, description="Insufficient data")
            
        ath = df['high'].max()
        curr = df['close'].iloc[-2]
        drawdown = (curr - ath) / ath
        
        # Scoring:
        # Deep Bear (drawdown < -70%) -> +10
        # Overheated (near ATH or new high) -> -5 to -10
        if drawdown < -0.7:
             score = 10.0
        elif drawdown > -0.1:
             score = -10.0
        else:
             # interpolation between -0.7 and -0.1
             # -0.7 -> 10, -0.4 -> 0, -0.1 -> -10
             score = ((-drawdown - 0.4) / 0.3) * 10
             
        return IndicatorResult(
            name="Cycle_Pos",
            score=round(score, 2),
            details={"drawdown": round(drawdown, 4), "ath": ath},
            description=f"Market is {abs(drawdown)*100:.1f}% off from ATH"
        )

if __name__ == "__main__":
    indicator = SentimentCycleIndicator()
    print(indicator.get_fear_greed_score())
    print(indicator.get_cycle_position_score())
