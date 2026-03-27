import pandas as pd
import time
from typing import Optional, Callable
from src.fetchers.binance_fetcher import BinanceFetcher
from src.fetchers.fred_fetcher import FredFetcher
from src.utils.retries import retry_with_backoff

class LiveDataProvider:
    """
    TADR Phase 2: Live Data Bridge
    Orchestrates multiple fetchers and performs cross-asset time alignment.
    Ensures 'BTC', 'SPX', and 'DXY' have a consistent timeline.
    """

    def __init__(self, binance: Optional[BinanceFetcher] = None, 
                 fred: Optional[FredFetcher] = None,
                 max_staleness_hours: int = 72):
        self.binance = binance or BinanceFetcher()
        self.fred = fred or FredFetcher()
        self.max_staleness_hours = max_staleness_hours

    def get_sync_market_data(self, window: int = 90) -> Optional[pd.DataFrame]:
        """
        Fetches and synchronizes multi-source market data.
        Returns a single DataFrame with synchronized Daily OHLCV/Rates.
        """
        # 1. Fetch BTC (Always 24/7)
        # Using a buffered fetch to ensure alignment
        btc_df = self._safe_fetch_btc(window + 30)
        if btc_df is None or len(btc_df) < window:
            return None
        
        btc_close = btc_df['close'].rename("BTC")
        latest_btc_time = btc_close.index[-1]

        # 2. Fetch Macro (Daily, Business days only)
        dxy_raw = self._safe_fetch_fred("DTWEXBGS", window + 40)
        spx_raw = self._safe_fetch_fred("SP500", window + 40)

        if dxy_raw is None or spx_raw is None:
            return None

        # 3. 数据新鲜度检查 (Staleness Check) [指令 2.1]
        # 检查宏观数据最后观测点是否落后于 BTC 太多
        latest_macro_time = min(dxy_raw.index[-1], spx_raw.index[-1])
        staleness_hours = (latest_btc_time - latest_macro_time).total_seconds() / 3600
        
        if staleness_hours > self.max_staleness_hours:
            print(f"[CIRCUIT_BREAKER] Macro data is too stale: {staleness_hours:.1f}h > {self.max_staleness_hours}h")
            print(f"[RCA_DATA] Latest BTC: {latest_btc_time} | Latest Macro: {latest_macro_time}")
            return None

        # 4. Synchronize on BTC Timeline (The superset)
        sync_df = pd.DataFrame(index=btc_close.index)
        sync_df = sync_df.join(btc_close)
        sync_df = sync_df.join(dxy_raw.rename("DXY"))
        sync_df = sync_df.join(spx_raw.rename("SPX"))

        # 5. Handle Gaps (FFILL macro for weekends/holidays)
        sync_df = sync_df.ffill()
        
        # 6. Final validation and windowing
        sync_df = sync_df.dropna().tail(window)
        
        if len(sync_df) < window:
            return None
            
        return sync_df

    @retry_with_backoff(retries=3)
    def _safe_fetch_btc(self, limit: int):
        return self.binance.fetch_ohlcv(limit=limit)

    @retry_with_backoff(retries=3)
    def _safe_fetch_fred(self, series_id: str, limit: int):
        return self.fred.get_series(series_id, limit=limit)
