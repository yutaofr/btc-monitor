import pandas as pd
import numpy as np
import requests
import yfinance as yf
from fredapi import Fred
from src.config import Config
from src.fetchers.blockchain_fetcher import BlockchainFetcher
from src.indicators.base import IndicatorResult, calculate_rsi

def _load_btc_daily(start=None, end=None):
    """Load BTC daily data with multiple fallbacks to ensure backtest stability."""
    df = pd.DataFrame()
    source = "none"
    
    # 1. YFinance
    try:
        if start or end:
            df = yf.download("BTC-USD", start=start, end=end, interval="1d", auto_adjust=False, progress=False)
        else:
            df = yf.download("BTC-USD", period="max", interval="1d", auto_adjust=False, progress=False)
        if not df.empty: source = "yfinance"
    except Exception:
        df = pd.DataFrame()

    # 2. CoinGecko Fallback
    if df.empty:
        try:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {"vs_currency": "usd", "days": "max", "interval": "daily"}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                prices = data.get("prices", [])
                df = pd.DataFrame(prices, columns=["timestamp", "close"])
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms").dt.tz_localize(None)
                df = df.set_index("datetime")
                df["open"] = df["close"]
                df["high"] = df["close"]
                df["low"] = df["close"]
                df["volume"] = 0
                source = "coingecko"
        except Exception:
            df = pd.DataFrame()

    # Final cleanup
    if df.empty:
        # Create an empty df with DatetimeIndex to prevent resample crashes
        empty_index = pd.DatetimeIndex([])
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"], index=empty_index), "none"

    df = df.rename(columns={c: c.lower().replace(" ", "_") for c in df.columns})
    df.index = pd.to_datetime(df.index)
    
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]
        
    df = df.dropna(subset=["close"])
    return df, source

def _to_weekly_ohlcv(daily_df):
    """Resample daily to weekly Friday closes."""
    if daily_df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"], index=pd.DatetimeIndex([]))
    weekly = daily_df.resample("W-FRI").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    })
    return weekly.dropna(subset=["open", "close"])

def _load_macro_series():
    """Load FRED macro data for historical scoring."""
    if not Config.FRED_API_KEY:
        return None, None
    fred = Fred(api_key=Config.FRED_API_KEY)
    
    try:
        walcl = fred.get_series("WALCL")
        tga = fred.get_series("WTREGEN")
        rrp = fred.get_series("RRPONTSYD")
        yields = fred.get_series("DGS10")
        
        walcl_w = walcl.resample("W-FRI").last()
        tga_w = tga.resample("W-FRI").last()
        rrp_w = rrp.resample("W-FRI").last()
        
        net_liq = walcl_w - tga_w - rrp_w
        yields_w = yields.resample("W-FRI").last()
        return net_liq, yields_w
    except Exception:
        return None, None

def _prepare_valuation_series(weekly_index):
    """Load and prepare MVRV and Puell for historical scoring."""
    fetcher = BlockchainFetcher()
    market_price_df = fetcher.fetch_chart("market-price", timespan="all")
    miners_revenue_df = fetcher.get_miners_revenue(timespan="all")
    
    mvrv_weekly = None
    puell_weekly = None
    
    if market_price_df is not None and not market_price_df.empty:
        mp = market_price_df["value"].resample("D").last().ffill()
        mvrv_daily = pd.DataFrame({"price": mp})
        mvrv_daily["ma_730"] = mvrv_daily["price"].rolling(window=730).mean()
        mvrv_weekly = mvrv_daily.resample("W-FRI").last().reindex(weekly_index).ffill()
        
    if miners_revenue_df is not None and not miners_revenue_df.empty:
        mr = miners_revenue_df["value"].resample("D").last().ffill()
        puell_daily = pd.DataFrame({"revenue": mr})
        puell_daily["ma_365"] = puell_daily["revenue"].rolling(window=365).mean()
        puell_weekly = puell_daily.resample("W-FRI").last().reindex(weekly_index).ffill()
        
    return mvrv_weekly, puell_weekly

def _score_technical(weekly, pi_weekly, rsi_weekly, idx):
    """Historical technical scoring logic for backtesting."""
    results = []
    close = weekly["close"].iloc[idx]
    
    wma_series = weekly["close"].rolling(window=200).mean()
    wma_200 = wma_series.iloc[idx]
    
    if pd.isna(wma_200):
        results.append(IndicatorResult("200WMA", 0, is_valid=False))
    else:
        ratio = float(close / wma_200)
        score = 10.0 if ratio <= 1.0 else max(-10.0, 10.0 - (ratio - 1.0) * 20.0)
        results.append(IndicatorResult("200WMA", float(round(score, 2)), details={"ratio": ratio}))
        
    sma_111 = pi_weekly["sma111"].iloc[idx]
    sma_350_x2 = pi_weekly["sma350x2"].iloc[idx]
    if pd.isna(sma_111) or pd.isna(sma_350_x2):
        results.append(IndicatorResult("Pi_Cycle", 0, is_valid=False))
    else:
        diff_ratio = float(sma_111 / sma_350_x2)
        score = -10.0 if diff_ratio >= 1.0 else (-5.0 if diff_ratio >= 0.9 else 5.0)
        results.append(IndicatorResult("Pi_Cycle", score, details={"ratio": diff_ratio}))
        
    if idx < 5 or pd.isna(rsi_weekly.iloc[idx]) or pd.isna(rsi_weekly.iloc[idx-5]):
        results.append(IndicatorResult("RSI_Div", 0, is_valid=False))
    else:
        curr_p, prev_p = float(weekly["close"].iloc[idx]), float(weekly["close"].iloc[idx-5])
        curr_r, prev_r = float(rsi_weekly.iloc[idx]), float(rsi_weekly.iloc[idx-5])
        if curr_p < prev_p and curr_r > prev_r: score = 10.0
        elif curr_p > prev_p and curr_r < prev_r: score = -10.0
        else: score = 0.0
        results.append(IndicatorResult("RSI_Div", score))
        
    return results

def _score_macro(net_liq, yields, idx):
    """Historical macro scoring logic for backtesting."""
    results = []
    if net_liq is None or yields is None or idx < 1:
        return [IndicatorResult(n, 0, is_valid=False) for n in ["Net_Liquidity", "Yields"]]
        
    curr_liq, prev_liq = net_liq.iloc[idx], net_liq.iloc[idx-1]
    if pd.isna(curr_liq) or pd.isna(prev_liq) or float(prev_liq) == 0:
        results.append(IndicatorResult("Net_Liquidity", 0, is_valid=False))
    else:
        change = float((curr_liq - prev_liq) / prev_liq * 100)
        score = 8.0 if change > 0.5 else (-8.0 if change < -0.5 else 2.0)
        results.append(IndicatorResult("Net_Liquidity", score, details={"change": change}))
        
    curr_y, prev_y = yields.iloc[idx], yields.iloc[idx-1]
    if pd.isna(curr_y) or pd.isna(prev_y):
        results.append(IndicatorResult("Yields", 0, is_valid=False))
    else:
        y_curr, y_prev = float(curr_y), float(prev_y)
        score = 5.0 if y_curr < y_prev else (-5.0 if y_curr > y_prev * 1.05 else 0.0)
        results.append(IndicatorResult("Yields", score))
        
    return results

def _score_valuation(mvrv_w, puell_w, idx):
    """Historical valuation scoring logic for backtesting."""
    results = []
    if mvrv_w is None or pd.isna(mvrv_w["ma_730"].iloc[idx]):
        results.append(IndicatorResult("MVRV_Proxy", 0, is_valid=False))
    else:
        ratio = float(mvrv_w["price"].iloc[idx] / mvrv_w["ma_730"].iloc[idx])
        if ratio <= 0.9: score = 10.0
        elif ratio >= 3.7: score = -10.0
        elif ratio <= 1.2: score = 8.0
        else: score = 8.0 - (ratio - 1.2) * (18.0 / 2.5)
        results.append(IndicatorResult("MVRV_Proxy", float(round(score, 2)), weight=1.5))
        
    if puell_w is None or pd.isna(puell_w["ma_365"].iloc[idx]):
        results.append(IndicatorResult("Puell_Multiple", 0, is_valid=False))
    else:
        puell = float(puell_w["revenue"].iloc[idx] / puell_w["ma_365"].iloc[idx])
        if puell <= 0.5: score = 10.0
        elif puell >= 4.0: score = -10.0
        elif puell <= 1.0: score = 10.0 - (puell - 0.5) * 16.0
        else: score = 2.0 - (puell - 1.0) * 4.0
        results.append(IndicatorResult("Puell_Multiple", float(round(score, 2)), weight=1.2))
        
    results.append(IndicatorResult("Production_Cost", 0, is_valid=False, details={"research_only": True}))
    return results

def _score_missing(name, description):
    """Utility for unavailable historical indicators."""
    return IndicatorResult(name, 0, description=description, is_valid=False)
