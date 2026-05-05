import pandas as pd
from datetime import datetime, timezone
from src.fetchers.blockchain_fetcher import BlockchainFetcher
from src.indicators.base import IndicatorResult
from src.strategy.factor_utils import quantize_score

class ValuationIndicator:
    """
    On-chain Fundamental Valuation Indicators (MVRV Proxy, Puell Multiple, Miner Cost).
    Designed to estimate "Fair Value" of BTC based on network activity and production.
    """
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or BlockchainFetcher()

    def get_puell_multiple_score(self):
        """
        Puell Multiple: Daily Miner Revenue / 365d Moving Average of Miner Revenue.
        Logic: Measures supply pressure from miners.
        """
        df = self.fetcher.get_miners_revenue(timespan="14months") # Need extra for MA
        if df is None or len(df) < 365:
            return IndicatorResult("Puell_Multiple", 0, description="Insufficient historical revenue data", is_valid=False)

        # Calculate 365-day moving average
        df['ma_365'] = df['value'].rolling(window=365).mean()
        
        current_rev = df['value'].iloc[-1]
        ma_365 = df['ma_365'].iloc[-1]
        
        if ma_365 == 0:
            return IndicatorResult("Puell_Multiple", 0, description="Zero MA in revenue", is_valid=False)
            
        puell = current_rev / ma_365
        
        # Scoring Logic:
        # < 0.5: Capitulation/Bottom (Extreme Bullish) -> +10
        # > 4.0: Market Overheated (Extreme Bearish) -> -10
        if puell <= 0.5:
            score = 10.0
        elif puell >= 4.0:
            score = -10.0
        elif puell <= 1.0:
            # Scale from 0.5 (10) to 1.0 (2)
            score = 10.0 - (puell - 0.5) * 16.0
        else:
            # Scale from 1.0 (2) to 4.0 (-10)
            score = 2.0 - (puell - 1.0) * 4.0
            
        return IndicatorResult(
            name="Puell_Multiple",
            score=quantize_score(score),
            details={"puell": quantize_score(puell), "revenue": quantize_score(current_rev)},
            description=f"Puell Multiple is {puell:.2f} ({'low' if puell < 1.0 else 'high'} revenue relative to year avg)",
            timestamp=datetime.now(timezone.utc)
        )

    def get_production_cost_score(self):
        """
        Estimate Bitcoin production cost (Fundamental Floor).
        Logic: Simplified A.S. Hayes Model (Energy Cost to mine 1 BTC).
        """
        stats = self.fetcher.get_current_stats()
        if not stats or "market_price_usd" not in stats or "hash_rate" not in stats:
            return IndicatorResult(
                "Production_Cost",
                0,
                details={"research_only": True},
                description="Research-only: stats unavailable",
                is_valid=False,
            )

        curr_price = stats["market_price_usd"]
        hash_rate = stats["hash_rate"] # Current GH/s from stats
        difficulty = stats["difficulty"]
        
        # 1. Estimate daily BTC issuance (Reward * Blocks/Day)
        # 10 min blocks -> 144 blocks/day. Current subsidy = 3.125 (post-halving)
        blocks_per_day = 144
        subsidy = 3.125 # Adjusted for 2026 post-halving context
        daily_issuance = blocks_per_day * subsidy
        
        # 2. Production Cost Estimate (simplified proxy):
        # We'll use Price/Hash-Rate relationship (Hash Price) relative to historical floor.
        # Alternatively, use Realized Price as a proxy if available.
        # For now, let's use the Price/Production ratio if we had a more robust model.
        # Since exact electricity/hardware is unknown, we use a heuristic:
        # Price is "fair" if it's near the 2-year average cost basis.
        
        # Fallback: Use the Price vs 2-year MA if we can't get a better cost model.
        # Let's try to find MVRV one more time in the engine.
        
        # Scoring: Neutral placeholder for now, focused on Puell and MVRV.
        # This remains surfaced in the report, but it is excluded from production scoring.
        return IndicatorResult(
            "Production_Cost",
            2.0,
            details={"research_only": True},
            description="Research-only: network fundamental floor placeholder is surfaced for reference",
            is_valid=False,
        )

    def get_mvrv_proxy_score(self, price=None):
        """
        MVRV Ratio: Market Cap / Realized Cap.
        Since realized-cap is hard to get for free, we use a high-correlation proxy:
        Price / 2-year Moving Average (Active Investor Cost Basis).
        """
        # Fetch long-term price data from Binance (already in TechnicalIndicator)
        # To avoid circular dependency, we'll implement a simple one here.
        # Or even better: fetch the 'market-price' chart from Blockchain.info
        df = self.fetcher.fetch_chart("market-price", timespan="3years")
        if df is None or len(df) < 730:
            return IndicatorResult("MVRV_Proxy", 0, description="Insufficient price data for 2yr MA", is_valid=False)
            
        # Calculate 2-year (730 days) MA
        df['ma_730'] = df['value'].rolling(window=730).mean()
        
        curr_price = price or df['value'].iloc[-1]
        cost_basis_proxy = df['ma_730'].iloc[-1]
        
        mvrv_proxy = curr_price / cost_basis_proxy
        
        # MVRV Scoring (Standardized):
        # < 1.0 (Price < Cost Basis): +10 (Accumulate)
        # > 3.7 (Historical Peak): -10 (Bubble)
        # 1.2 - 2.0: Healthy Growth
        if mvrv_proxy <= 0.9:
            score = 10.0
        elif mvrv_proxy >= 3.7:
            score = -10.0
        elif mvrv_proxy <= 1.2:
            score = 8.0
        else:
            # Linear scaling from 1.2 (8) to 3.7 (-10)
            score = 8.0 - (mvrv_proxy - 1.2) * (18.0 / 2.5)
            
        return IndicatorResult(
            name="MVRV_Proxy",
            score=quantize_score(score),
            details={"mvrv_proxy": quantize_score(mvrv_proxy), "cost_basis": quantize_score(cost_basis_proxy)},
            description=f"Price is {mvrv_proxy:.2f}x of 2-year cost basis proxy",
            timestamp=datetime.now(timezone.utc)
        )

    def get_hash_ribbon_score(self):
        """
        Evaluate Hash Ribbon signal.
        Logic: 30d/60d hash rate moving averages.
        """
        from src.indicators.miner_cycle import calculate_hash_ribbon
        df_hash = self.fetcher.get_hash_rate(timespan="3months")
        return calculate_hash_ribbon(df_hash)

if __name__ == "__main__":
    indicator = ValuationIndicator()
    print(indicator.get_puell_multiple_score())
    print(indicator.get_mvrv_proxy_score())
