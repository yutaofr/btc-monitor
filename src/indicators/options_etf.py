import yfinance as yf
import pandas as pd
from src.indicators.base import IndicatorResult
from src.fetchers.binance_fetcher import BinanceFetcher

class OptionsETFIndicator:
    def __init__(self, binance_fetcher=None):
        self.binance_fetcher = binance_fetcher or BinanceFetcher()

    def get_options_wall_score(self, ticker_symbol="BITO"):
        """
        Estimate Put Wall for Bitcoin via BITO proxy.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Use closest expiration as a sample
            expirations = ticker.options
            if not expirations:
                 return IndicatorResult("Options_Wall", 0, description="No option data")
            
            opt = ticker.option_chain(expirations[0])
            puts = opt.puts.fillna(0)
            
            if puts.empty:
                return IndicatorResult("Options_Wall", 0, description="No put data")
                
            # Find Strike with Max Open Interest
            max_oi_put = puts.loc[puts['openInterest'].idxmax()]
            put_wall_strike = max_oi_put['strike']
            
            # BITO is ~1/1000 or ~1/10 of BTC price depending on split. 
            # We care about the relative proximity of the current price.
            curr_price = ticker.fast_info['lastPrice']
            distance = (curr_price - put_wall_strike) / put_wall_strike
            
            if 0 <= distance <= 0.05:
                score = 5.0 # Near support
                desc = f"Price near Put Wall support at {put_wall_strike}"
            elif distance < 0:
                score = 8.0 # Oversold below wall
                desc = "Price below Put Wall (Oversold)"
            else:
                score = 2.0
                desc = "Neutral distance from Put Wall"
                
            return IndicatorResult(
                name="Options_Wall",
                score=score,
                details={"strike": put_wall_strike, "distance": distance},
                description=desc
            )
        except Exception as e:
            print(f"[ERROR] Options Wall calculation failed: {e}")
            return IndicatorResult("Options_Wall", 0, description="Error fetching options")

    def get_etf_flow_divergence_score(self, etf_symbol="IBIT"):
        """
        Detect divergence: Price down + ETF Volume spike/AUM proxy up.
        Logic: Use confirmed daily data.
        """
        try:
            # Get BTC Daily
            df_btc = self.binance_fetcher.fetch_ohlcv(timeframe="1d", limit=10)
            # Get ETF Daily
            df_etf = yf.download(etf_symbol, period="10d", interval="1d", progress=False)
            
            if df_btc is None or df_etf.empty:
                return IndicatorResult("ETF_Flow", 0, description="Missing data")

            # Check last 3 days
            price_trend = df_btc['close'].iloc[-1] / df_btc['close'].iloc[-4]
            # Volume is a rough proxy for interest/flow spike
            vol_trend = df_etf['Volume'].iloc[-1] / df_etf['Volume'].rolling(window=5).mean().iloc[-1]
            
            score = 0
            if price_trend < 0.97 and vol_trend > 1.3:
                score = 10.0 # Price down 3%, Volume up 30% -> Accumulation?
                desc = "Strong Accumulation Divergence (Price Down, ETF Volume Up)"
            elif price_trend > 1.05 and vol_trend < 0.7:
                 score = -5.0 # Price up, Volume drying up -> Exhaustion?
                 desc = "Price Up, ETF Volume Exhaustion"
            else:
                score = 0
                desc = "No clear ETF divergence"
                
            return IndicatorResult(
                name="ETF_Flow",
                score=score,
                details={"price_trend": price_trend, "vol_trend": vol_trend},
                description=desc
            )
        except Exception as e:
            print(f"[ERROR] ETF Flow Divergence failed: {e}")
            return IndicatorResult("ETF_Flow", 0, description="Error fetching ETF data")

if __name__ == "__main__":
    indicator = OptionsETFIndicator()
    print(indicator.get_options_wall_score())
    print(indicator.get_etf_flow_divergence_score())
