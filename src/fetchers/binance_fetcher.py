import ccxt
import pandas as pd
import logging
from typing import Optional, List, Dict, Any

# Setup Logging
logger = logging.getLogger("MarketFetcher")

class BinanceFetcher:
    """
    Zero-Intrusive Market Data Fetcher.
    Optimized for GitHub Actions: Automatically falls back to Kraken/Coinbase 
    if Binance is restricted (HTTP 451) in the execution environment.
    """
    def __init__(self):
        # Primary: Binance Global
        self.primary = ccxt.binance({
            'enableRateLimit': True,
        })
        # Alias for backward compatibility with unit tests
        self.exchange = self.primary
        
        # Fallbacks (More permissive for GHA runners)
        self.fallbacks = {
            'kraken': ccxt.kraken({'enableRateLimit': True}),
            'coinbase': ccxt.coinbase({'enableRateLimit': True})
        }

    def _execute_with_fallback(self, func_name: str, symbol: str, *args, **kwargs):
        """
        Executes a fetch method across multiple exchanges if the primary fails 
        with a location restriction or permission error.
        """
        # 1. Try Primary (Binance)
        try:
            method = getattr(self.primary, func_name)
            return method(symbol, *args, **kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            if "restricted location" in err_msg or "451" in err_msg or "permission denied" in err_msg:
                logger.warning(f"[RECOVERY] Binance restricted (451/403). Initiating fallback sequence for {symbol}...")
            else:
                # Other errors (e.g. rate limit) we still try fallback but log as error
                logger.error(f"[ERROR] Binance primary fetch failed: {e}. Trying fallback...")

        # 2. Try Fallbacks
        for name, exchange in self.fallbacks.items():
            # Translate symbol if needed (USDT -> USD for Kraken/Coinbase)
            target_symbol = symbol.replace("USDT", "USD") if "USDT" in symbol else symbol
            try:
                logger.info(f"[ACTION] Attempting fetch via {name} for {target_symbol}...")
                method = getattr(exchange, func_name)
                return method(target_symbol, *args, **kwargs)
            except Exception as e:
                logger.warning(f"[RECOVERY] Fallback {name} failed: {e}")
                continue
        
        return None

    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1d", limit=100):
        """Fetch historical OHLCV data with transparent failover."""
        ohlcv = self._execute_with_fallback('fetch_ohlcv', symbol, timeframe=timeframe, limit=limit)
        if ohlcv is None:
            return None
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def fetch_full_history(self, symbol="BTC/USDT", timeframe="1d", since_iso="2016-01-01T00:00:00Z"):
        """
        Fetch full history. Note: Fallback exchanges may have different history depths.
        """
        # Try primary logic first
        try:
            since = self.primary.parse8601(since_iso)
            all_ohlcv = []
            # We don't use full _execute_with_fallback for pagination to keep it simple,
            # but if the first call fails, we switch exchange entirely.
            
            curr_exchange = self.primary
            curr_symbol = symbol
            
            try:
                test_call = curr_exchange.fetch_ohlcv(curr_symbol, timeframe=timeframe, limit=1)
            except Exception as e:
                if "451" in str(e) or "restricted" in str(e).lower():
                    # Switch to Kraken for history
                    curr_exchange = self.fallbacks['kraken']
                    curr_symbol = symbol.replace("USDT", "USD")
                    logger.warning(f"[RECOVERY] Switching history fetch to {curr_exchange.id}")
            
            while True:
                ohlcv = curr_exchange.fetch_ohlcv(curr_symbol, timeframe=timeframe, since=since)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                if len(ohlcv) < 100:
                    break
                import time
                time.sleep(curr_exchange.rateLimit / 1000)
            
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"[ERROR] Failed full history fetch: {e}")
            return None

    def get_current_price(self, symbol="BTC/USDT"):
        """Get latest ticker price with transparent failover."""
        ticker = self._execute_with_fallback('fetch_ticker', symbol)
        if ticker is None:
            return None
        return ticker['last']

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = BinanceFetcher()
    print("Testing Daily OHLCV Fetch (Triggering fallback if needed)...")
    df = fetcher.fetch_ohlcv(limit=5)
    if df is not None:
        print(df.tail())
    else:
        print("Final result: None (All exchanges restricted)")
