import pandas as pd
from src.fetchers.fred_fetcher import FredFetcher
from src.indicators.base import IndicatorResult

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
            score=score,
            details={"change_pct": round(change_pct, 4), "current": current_liq},
            description=f"Liquidity is {'expanding' if score > 0 else 'contracting'}"
        )

    def get_yield_divergence_score(self):
        """
        Monitor US10Y (Yields) as a regime.
        High/rising yields = Bad for Risk assets. Falling = Good.
        """
        yields = self.fetcher.get_us10y()
        if yields is None or len(yields) < 3:
            return IndicatorResult("Yields", 0, description="Insufficient data", is_valid=False)

        curr_yield = yields.iloc[-1]
        
        # Simple regime check: current vs SMA (or just simple trend if not enough data)
        sma = yields.mean()
        
        if curr_yield < sma:
            score = 5.0 # Yields falling below moving average, favorable regime
            desc = "falling regime"
        elif curr_yield > sma * 1.02:
            score = -5.0 # Yields rising above moving average, tight regime
            desc = "rising regime"
        else:
            score = 0
            desc = "stable regime"
            
        return IndicatorResult(
            name="Yields",
            score=score,
            details={"current": curr_yield, "sma": sma, "regime": desc},
            description=f"Yields are in a {desc}"
        )

    def get_dxy_regime_score(self):
        """
        Evaluate DXY (Dollar Index) regime.
        Falling dollar = Bullish for BTC. Rising dollar = Bearish.
        """
        dxy = self.fetcher.get_dxy()
        if dxy is None or len(dxy) < 3:
            return IndicatorResult("DXY_Regime", 0, description="Insufficient data", is_valid=False)

        curr_dxy = dxy.iloc[-1]
        sma = dxy.mean()
        
        if curr_dxy < sma:
            score = 6.0 # DXY falling
            desc = "falling regime"
        elif curr_dxy > sma:
            score = -6.0 # DXY rising
            desc = "rising regime"
        else:
            score = 0
            desc = "stable regime"
            
        return IndicatorResult(
            name="DXY_Regime",
            score=score,
            details={"current": curr_dxy, "sma": sma, "regime": desc},
            description=f"DXY is in a {desc}"
        )

if __name__ == "__main__":
    indicator = MacroIndicator()
    print(indicator.get_net_liquidity_score())
