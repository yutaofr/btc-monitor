import pandas as pd
import numpy as np
from datetime import datetime, timezone
from src.fetchers.binance_fetcher import BinanceFetcher
from src.indicators.base import IndicatorResult, calculate_rsi

class TechnicalIndicator:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or BinanceFetcher()

    def get_200wma_score(self):
        """
        Calculate score based on distance from 200WMA.
        Logic: Use confirmed weekly close (index -2).
        """
        df_weekly = self.fetcher.fetch_ohlcv(timeframe="1w", limit=210)
        if df_weekly is None or len(df_weekly) < 200:
            return IndicatorResult("200WMA", 0, description="Insufficient data", is_valid=False)

        # Use index -2 to avoid the currently forming weekly bar (index -1)
        confirmed_close = df_weekly.iloc[-2]['close']
        wma_200 = df_weekly['close'].iloc[:-1].rolling(window=200).mean().iloc[-1]
        
        ratio = confirmed_close / wma_200
        
        # Scoring logic: 
        # ratio <= 1.0 (at or below 200WMA) -> +10
        # ratio >= 2.0 (bubble) -> -10
        if ratio <= 1.0:
            score = 10.0
        else:
            score = max(-10.0, 10.0 - (ratio - 1.0) * 20.0)
            
        return IndicatorResult(
            name="200WMA",
            score=round(score, 2),
            details={"close": confirmed_close, "200wma": wma_200, "ratio": ratio},
            description=f"Price is {ratio:.2f}x of 200WMA",
            timestamp=datetime.now(timezone.utc)
        )

    def get_pi_cycle_score(self):
        """
        Pi Cycle Bottom Indicator: 471 SMA and 150 EMA (approx). 
        Actual Pi Cycle Top: 111DMA and 2*350DMA.
        We'll use Pi Cycle Top crossover as a sell signal.
        """
        df_daily = self.fetcher.fetch_ohlcv(timeframe="1d", limit=750)
        if df_daily is None or len(df_daily) < 700:
             return IndicatorResult("Pi_Cycle", 0, description="Insufficient data", is_valid=False)

        sma_111 = df_daily['close'].rolling(window=111).mean().iloc[-1]
        sma_350_x2 = df_daily['close'].rolling(window=350).mean().iloc[-1] * 2
        
        # If 111DMA > 2*350DMA -> Highly Overheated
        diff_ratio = sma_111 / sma_350_x2
        if diff_ratio >= 1.0:
            score = -10.0
        elif diff_ratio >= 0.9:
            score = -5.0
        else:
            score = 5.0 # Healthy distance
            
        return IndicatorResult(
            name="Pi_Cycle",
            score=score,
            details={"111dma": sma_111, "350dma_x2": sma_350_x2},
            description="Pi Cycle Top gap is healthy" if score > 0 else "Pi Cycle Top imminent",
            timestamp=datetime.now(timezone.utc)
        )

    def get_rsi_divergence_score(self):
        """
        Check for weekly RSI divergence.
        """
        df_weekly = self.fetcher.fetch_ohlcv(timeframe="1w", limit=50)
        if df_weekly is None or len(df_weekly) < 30:
            return IndicatorResult("RSI_Div", 0, description="Insufficient data", is_valid=False)
            
        closes = df_weekly['close'].iloc[:-1] # Use confirmed ones
        rsi = calculate_rsi(closes)
        
        curr_price = closes.iloc[-1]
        prev_price = closes.iloc[-5] # Compare to ~month ago
        curr_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-5]
        
        score = 0
        if curr_price < prev_price and curr_rsi > prev_rsi:
            score = 10.0 # Bullish divergence
            desc = "Bullish Weekly RSI Divergence"
        elif curr_price > prev_price and curr_rsi < prev_rsi:
            score = -10.0 # Bearish divergence
            desc = "Bearish Weekly RSI Divergence"
        else:
            score = 0
            desc = "No RSI Divergence"
            
        return IndicatorResult(
            name="RSI_Div",
            score=score,
            details={"curr_rsi": curr_rsi, "prev_rsi": prev_rsi},
            description=desc,
            timestamp=datetime.now(timezone.utc)
        )

    def get_short_term_stretch_score(self):
        """
        Evaluate short-term exhaustion (Price vs 26-week / 182-day EMA).
        Logic from ADD: 4-week price stretch vs 26-week trend anchor.
        """
        df_daily = self.fetcher.fetch_ohlcv(timeframe="1d", limit=200)
        if df_daily is None or len(df_daily) < 182:
            return IndicatorResult("Short_Term_Stretch", 0, description="Insufficient data", is_valid=False)
            
        curr_price = df_daily.iloc[-1]['close']
        ema_26w = df_daily['close'].ewm(span=182).mean().iloc[-1]
        
        ratio = curr_price / ema_26w
        
        # If price is > 1.2x (20% stretch) -> Overheated
        # If price is < 0.8x (20% discount) -> Bullish
        if ratio >= 1.25:
            score = -8.0
        elif ratio <= 0.8:
            score = 8.0
        else:
            score = 0.0
            
        return IndicatorResult(
            name="Short_Term_Stretch",
            score=score,
            details={"current": curr_price, "ema_26w": ema_26w, "ratio": ratio},
            description=f"Price stretch vs 26w EMA is {ratio:.2f}x",
            timestamp=datetime.now(timezone.utc)
        )

if __name__ == "__main__":
    indicator = TechnicalIndicator()
    print("Testing 200WMA...")
    print(indicator.get_200wma_score())
    print("Testing Stretch...")
    print(indicator.get_short_term_stretch_score())
