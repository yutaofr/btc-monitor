import pandas as pd
from datetime import datetime, timezone
from src.fetchers.fred_fetcher import FredFetcher
from src.indicators.base import IndicatorResult
from src.strategy.factor_utils import quantize_score

class MacroIndicator:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or FredFetcher()

    def get_net_liquidity_score(self):
        """
        Evaluate Net Liquidity trend.
        Logic: Momentum of (WALCL - TGA - RRP).
        """
        df = self.fetcher.get_net_liquidity()
        if df is None or len(df) < 2:
            return IndicatorResult("Net_Liquidity", 0, description="Insufficient data", is_valid=False)

        # Calculate momentum (Change over the last 2 records)
        current_liq = df["net_liquidity"].iloc[-1]
        prev_liq = df["net_liquidity"].iloc[-2]
        
        change_pct = (current_liq - prev_liq) / prev_liq * 100
        
        # Scoring: 
        # Expansion (> 0.5% weekly) -> +8
        # Contraction (< -0.5% weekly) -> -8
        # Otherwise -> neutral
        if change_pct > 0.5:
            score = 8.0
        elif change_pct < -0.5:
            score = -8.0
        else:
            score = 2.0 # Slight positive drift preferred for BTC
            
        return IndicatorResult(
            name="Net_Liquidity",
            score=quantize_score(score),
            details={"change_pct": quantize_score(change_pct), "current": current_liq},
            description=f"Liquidity is {'expanding' if score > 0 else 'contracting'}",
            timestamp=datetime.now(timezone.utc)
        )

    def get_yield_divergence_score(self):
        """
        Evaluate US10Y (Yields) through a 30/90-day SMA regime.
        Falling (30 < 90) = Bullish (+6.0). Rising (30 > 90) = Bearish (-6.0).
        """
        yields = self.fetcher.get_us10y()
        if yields is None or len(yields) < 90:
            return IndicatorResult("Yields", 0, description="Insufficient data", is_valid=False)

        sma30 = yields.rolling(window=30).mean().iloc[-1]
        sma90 = yields.rolling(window=90).mean().iloc[-1]
        
        if pd.isna(sma30) or pd.isna(sma90):
            return IndicatorResult("Yields", 0, description="SMA calculation failed", is_valid=False)

        if sma30 < sma90:
            score = 6.0 
            desc = "falling regime (30d < 90d SMA)"
        else:
            score = -6.0
            desc = "rising regime (30d > 90d SMA)"
            
        return IndicatorResult(
            name="Yields",
            score=quantize_score(score),
            details={"current": yields.iloc[-1], "sma30": quantize_score(sma30), "sma90": quantize_score(sma90)},
            description=f"Yields are in a {desc}",
            timestamp=datetime.now(timezone.utc)
        )

    def get_dxy_regime_score(self):
        """
        Evaluate DXY (Dollar Index) through a 30/90-day SMA regime.
        Falling dollar = Bullish (+6.0). Rising dollar = Bearish (-6.0).
        """
        dxy = self.fetcher.get_dxy()
        if dxy is None or len(dxy) < 90:
            return IndicatorResult("DXY_Regime", 0, description="Insufficient data", is_valid=False)

        sma30 = dxy.rolling(window=30).mean().iloc[-1]
        sma90 = dxy.rolling(window=90).mean().iloc[-1]
        
        if pd.isna(sma30) or pd.isna(sma90):
            return IndicatorResult("DXY_Regime", 0, description="SMA calculation failed", is_valid=False)

        if sma30 < sma90:
            score = 6.0 
            desc = "falling regime (30d < 90d SMA)"
        else:
            score = -6.0
            desc = "rising regime (30d > 90d SMA)"
            
        return IndicatorResult(
            name="DXY_Regime",
            score=quantize_score(score),
            details={"current": dxy.iloc[-1], "sma30": quantize_score(sma30), "sma90": quantize_score(sma90)},
            description=f"DXY is in a {desc}",
            timestamp=datetime.now(timezone.utc)
        )

if __name__ == "__main__":
    indicator = MacroIndicator()
    print(indicator.get_net_liquidity_score())
