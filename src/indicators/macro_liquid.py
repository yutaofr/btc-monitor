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
            return IndicatorResult("Net_Liquidity", 0, description="Insufficient data")

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
        Monitor US10Y (Yields). High yields = Bad for Risk assets.
        """
        yields = self.fetcher.get_us10y()
        if yields is None or len(yields) < 5:
            return IndicatorResult("Yields", 0, description="Insufficient data")

        curr_yield = yields.iloc[-1]
        prev_yield = yields.iloc[-5] # Week over Week
        
        if curr_yield < prev_yield:
            score = 5.0 # Yields falling, good for BTC
        elif curr_yield > prev_yield * 1.05:
            score = -5.0 # Yields spiking
        else:
            score = 0
            
        return IndicatorResult(
            name="Yields",
            score=score,
            details={"current": curr_yield, "prev": prev_yield},
            description=f"Yields are {'falling' if score > 0 else 'rising/stable'}"
        )

if __name__ == "__main__":
    indicator = MacroIndicator()
    print(indicator.get_net_liquidity_score())
