from fredapi import Fred
from src.config import Config
import pandas as pd

class FredFetcher:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.FRED_API_KEY
        self.fred = Fred(api_key=self.api_key) if self.api_key else None

    def get_series(self, series_id, limit=10):
        """Fetch raw series data from FRED."""
        if not self.fred:
            return None
        try:
            data = self.fred.get_series(series_id)
            return data.tail(limit)
        except Exception as e:
            print(f"[ERROR] Failed to fetch FRED series {series_id}: {e}")
            return None

    def get_net_liquidity(self):
        """
        Calculate Net Liquidity: Fed Balance Sheet - TGA - Reverse Repo
        Series used:
        - WALCL: Assets: Total Assets: Total Assets (Weekly)
        - WTREGEN: Treasury General Account (Weekly)
        - RRPONTSYD: Overnight Reverse Repurchase Agreements (Daily)
        """
        walcl = self.get_series("WALCL", limit=5)
        tga = self.get_series("WTREGEN", limit=5)
        rrp = self.get_series("RRPONTSYD", limit=30) # Daily, need more for overlap
        
        if walcl is None or tga is None or rrp is None:
            return None

        # Align to same frequency (Weekly approx)
        df = pd.DataFrame({
            "walcl": walcl,
            "tga": tga,
            "rrp": rrp.resample('W-WED').last() # RRP is daily, align to Fed's Wednesday pulse
        }).dropna()
        
        if df.empty:
            return None
            
        df["net_liquidity"] = df["walcl"] - df["tga"] - df["rrp"]
        return df

    def get_us10y(self):
        """Fetch 10-Year Treasury Constant Maturity Rate"""
        return self.get_series("DGS10", limit=60) # Increased limit for SMA

    def get_dxy(self):
        """Fetch US Dollar Index (Trade Weighted)"""
        return self.get_series("DTWEXBGS", limit=60) # Using Trade Weighted U.S. Dollar Index: Broad, Goods and Services

if __name__ == "__main__":
    fetcher = FredFetcher()
    print("Testing Net Liquidity Fetch...")
    res = fetcher.get_net_liquidity()
    if res is not None:
        print(res.tail())
