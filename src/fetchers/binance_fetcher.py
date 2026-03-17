import ccxt
import pandas as pd

class BinanceFetcher:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
        })

    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1d", limit=100):
        """Fetch historical OHLCV data."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"[ERROR] Failed to fetch {timeframe} OHLCV from Binance: {e}")
            return None

    def get_current_price(self, symbol="BTC/USDT"):
        """Get latest ticker price."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"[ERROR] Failed to fetch current price: {e}")
            return None

if __name__ == "__main__":
    fetcher = BinanceFetcher()
    print("Testing Daily OHLCV Fetch...")
    df = fetcher.fetch_ohlcv(limit=5)
    if df is not None:
        print(df)
