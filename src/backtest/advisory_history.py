import pandas as pd
import numpy as np
import os
import requests
from src.config import Config
from src.fetchers.blockchain_fetcher import BlockchainFetcher
from src.fetchers.binance_fetcher import BinanceFetcher
from src.fetchers.fred_fetcher import FredFetcher
from src.indicators.base import IndicatorResult, calculate_rsi

def _load_btc_daily(start_iso="2016-01-01T00:00:00Z"):
    """Load real BTC daily data from Binance with local fallback."""
    df = pd.DataFrame()
    source = "binance"
    
    try:
        # Check local cache first to avoid rate limits
        path = "data/btc_daily.csv"
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            source = "local_csv"
        else:
            fetcher = BinanceFetcher()
            df = fetcher.fetch_full_history(since_iso=start_iso)
            if df is not None and not df.empty:
                os.makedirs("data", exist_ok=True)
                df.to_csv(path)
    except Exception as e:
        print(f"[ERROR] Real BTC data load failed: {e}")
        
    return df, source

def _to_weekly_ohlcv(daily_df):
    """Convert daily to weekly OHLCV."""
    if daily_df is None or daily_df.empty: return pd.DataFrame()
    return daily_df.resample("W-FRI").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    })

def _load_macro_series(index):
    """Load REAL macro series from FRED aligned with the provided index."""
    if not Config.FRED_API_KEY:
        return None, None
        
    try:
        fetcher = FredFetcher()
        # FredFetcher.get_series defaults to 10, we need more for 10 years
        # But FredFetcher.get_net_liquidity is hardcoded to short limits
        # I'll use raw fredapi access here for backtest depth
        from fredapi import Fred
        fred = Fred(api_key=Config.FRED_API_KEY)
        
        walcl = fred.get_series("WALCL")
        tga = fred.get_series("WTREGEN")
        rrp = fred.get_series("RRPONTSYD")
        yields = fred.get_series("DGS10")
        
        walcl_w = walcl.resample("W-FRI").last()
        tga_w = tga.resample("W-FRI").last()
        rrp_w = rrp.resample("W-FRI").last()
        
        net_liq = (walcl_w - tga_w - rrp_w).reindex(index).ffill().bfill()
        yields_w = yields.resample("W-FRI").last().reindex(index).ffill().bfill()
        
        return net_liq, yields_w
    except Exception as e:
        print(f"[ERROR] Macro data fetch failed: {e}")
        return None, None

def _prepare_valuation_series(index):
    """Prepares valuation series (MVRV, Puell) from REAL Blockchain.info data."""
    try:
        fetcher = BlockchainFetcher()
        timespan = "10years"
        # market-cap and miners-revenue were tested and working
        m_cap = fetcher.get_market_cap(timespan=timespan)
        rev = fetcher.get_miners_revenue(timespan=timespan)
        
        if m_cap is None or rev is None:
            return None, None
            
        # Reindex and handle sparse data
        m_cap_s = m_cap["value"].reindex(index).ffill()
        rev_s = rev["value"].reindex(index).ffill()
        
        # Calculate proxies based on available data
        # MVRV Proxy: price / 2-year MA price (approximate from market-cap chart)
        mvrv_df = pd.DataFrame({
            "price": m_cap_s,
            "ma_730": m_cap_s.rolling(104).mean() # 104 weeks = 2 years
        }).ffill().bfill()
        
        # Puell: revenue / 1-year MA revenue
        puell_df = pd.DataFrame({
            "revenue": rev_s,
            "ma_365": rev_s.rolling(52).mean() # 52 weeks = 1 year
        }).ffill().bfill()
        
        return mvrv_df, puell_df
    except Exception as e:
        print(f"[ERROR] Valuation data fetch failed: {e}")
        return None, None

def _score_technical(weekly, rsi_weekly, idx):
    """Score technical indicators based on REAL data."""
    results = []
    
    # 200WMA
    price = float(weekly["close"].iloc[idx])
    ma200 = weekly["close"].rolling(200).mean().iloc[idx]
    if pd.isna(ma200):
        results.append(IndicatorResult("200WMA", 0.0, is_valid=False))
    else:
        ratio = price / ma200
        if ratio <= 1.0: score = 10.0
        elif ratio >= 3.0: score = -10.0
        else: score = 10.0 - (ratio - 1.0) * (20.0 / 2.0)
        results.append(IndicatorResult("200WMA", round(score, 2)))
        
    # RSI Weekly
    rsi = rsi_weekly.iloc[idx]
    if pd.isna(rsi):
        results.append(IndicatorResult("RSI_Weekly", 0.0, is_valid=False))
    else:
        if rsi <= 30: score = 10.0
        elif rsi >= 85: score = -10.0
        elif rsi <= 50: score = 8.0
        else: score = 8.0 - (rsi - 50) * (18.0 / 35.0)
        results.append(IndicatorResult("RSI_Weekly", round(score, 2)))
        
    return results

def _score_macro(net_liq, yields, idx):
    """Score macro indicators based on REAL data."""
    if net_liq is None or yields is None:
        return [
            IndicatorResult("Net_Liquidity", 0.0, is_valid=False),
            IndicatorResult("Yields", 0.0, is_valid=False)
        ]
        
    results = []
    # Liquidity vs 12m MA
    try:
        curr_liq = net_liq.iloc[idx]
        ma_liq = net_liq.rolling(52).mean().iloc[idx]
        if pd.isna(ma_liq):
            results.append(IndicatorResult("Net_Liquidity", 0.0, is_valid=False))
        else:
            ratio = curr_liq / ma_liq
            if ratio >= 1.1: score = 10.0
            elif ratio <= 0.9: score = -10.0
            else: score = (ratio - 1.0) * (20.0 / 0.2)
            results.append(IndicatorResult("Net_Liquidity", round(score, 2)))
    except Exception:
        results.append(IndicatorResult("Net_Liquidity", 0.0, is_valid=False))
        
    # Yields level
    try:
        y = yields.iloc[idx]
        if pd.isna(y):
            results.append(IndicatorResult("Yields", 0.0, is_valid=False))
        else:
            if y <= 1.5: score = 10.0
            elif y >= 5.5: score = -10.0
            else: score = 5.0 - (y - 3.5) * (15.0 / 2.0)
            results.append(IndicatorResult("Yields", round(score, 2)))
    except Exception:
        results.append(IndicatorResult("Yields", 0.0, is_valid=False))
        
    return results

def _score_valuation(mvrv_w, puell_w, idx):
    """Score valuation indicators based on REAL data."""
    if mvrv_w is None or puell_w is None:
        return [
            IndicatorResult("MVRV_Proxy", 0.0, is_valid=False),
            IndicatorResult("Puell_Multiple", 0.0, is_valid=False)
        ]
        
    results = []
    # MVRV Proxy
    try:
        ratio = float(mvrv_w["price"].iloc[idx] / mvrv_w["ma_730"].iloc[idx])
        if ratio <= 0.9: score = 10.0
        elif ratio >= 3.7: score = -10.0
        else: score = 8.0 - (ratio - 1.2) * (18.0 / 2.5)
        results.append(IndicatorResult("MVRV_Proxy", round(score, 2)))
    except Exception:
        results.append(IndicatorResult("MVRV_Proxy", 0.0, is_valid=False))
        
    # Puell
    try:
        ratio = float(puell_w["revenue"].iloc[idx] / puell_w["ma_365"].iloc[idx])
        if ratio <= 0.5: score = 10.0
        elif ratio >= 2.5: score = -10.0
        else: score = 6.0 - (ratio - 1.0) * (16.0 / 1.5)
        results.append(IndicatorResult("Puell_Multiple", round(score, 2)))
    except Exception:
        results.append(IndicatorResult("Puell_Multiple", 0.0, is_valid=False))
        
    return results

def _prepare_fng_series(index):
    """Fetch historical Fear & Greed data from Alternative.me."""
    try:
        url = "https://api.alternative.me/fng/?limit=0"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if "data" not in data:
            return None
            
        fng_list = data["data"]
        df = pd.DataFrame(fng_list)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["value"] = pd.to_numeric(df["value"])
        df.set_index("timestamp", inplace=True)
        
        # Sort by index and reindex to match backtest timeline
        df.sort_index(inplace=True)
        return df["value"].reindex(index).ffill().bfill()
    except Exception as e:
        print(f"[ERROR] FnG historical fetch failed: {e}")
        return None

def fetch_prices():
    """Real price fetcher for main entry point."""
    df, _ = _load_btc_daily()
    return df["close"] if df is not None and not df.empty else None

def evaluate_history():
    """Backtesting entry point for data fetching."""
    df, _ = _load_btc_daily()
    return df
