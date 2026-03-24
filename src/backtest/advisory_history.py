import pandas as pd
import numpy as np
import os
from src.config import Config
from src.indicators.base import IndicatorResult
def _load_macro_series(index):
    if not Config.FRED_API_KEY:
        return None, None, None
    try:
        from fredapi import Fred
        fred = Fred(api_key=Config.FRED_API_KEY)
        # WALCL (Fed Assets), DGS10 (10Y Yield), DTWEXBGS (Broad Dollar)
        walcl = fred.get_series("WALCL", observation_start="2010-01-01")
        yields = fred.get_series("DGS10", observation_start="2010-01-01")
        dxy = fred.get_series("DTWEXBGS", observation_start="2010-01-01")
        if dxy is None or dxy.empty:
            dxy = fred.get_series("DTWEXAFEGS", observation_start="2010-01-01")
            
        df = pd.DataFrame({"walcl": walcl, "yields": yields, "dxy": dxy}).ffill().bfill()
        df = df.resample("D").mean().ffill().bfill()
        
        return df["walcl"].reindex(index).ffill().bfill(), \
               df["yields"].reindex(index).ffill().bfill(), \
               df["dxy"].reindex(index).ffill().bfill()
    except Exception as e:
        print(f"[ERROR] Macro data fetch failed: {e}")
        return None, None, None

def _prepare_valuation_series(index):
    from src.fetchers.blockchain_fetcher import BlockchainFetcher
    try:
        fetcher = BlockchainFetcher()
        timespan = "10years"
        m_cap = fetcher.get_market_cap(timespan)
        rev = fetcher.get_miners_revenue(timespan)
        hash_rate = fetcher.get_hash_rate(timespan)
        
        # Fallbacks for missing charts
        if it_any_is_none := [m_cap is None, rev is None, hash_rate is None]:
            if m_cap is None: print("[ERROR] Market Cap fetch failed")
            if rev is None: print("[ERROR] Revenue fetch failed")
            if hash_rate is None: print("[ERROR] Hashrate fetch failed")
            
        m_cap_d = m_cap["value"].resample("D").mean().ffill() if m_cap is not None else None
        rev_d = rev["value"].resample("D").mean().ffill() if rev is not None else None
        hash_d = hash_rate["value"].resample("D").mean().ffill() if hash_rate is not None else None
        
        return pd.DataFrame({"m_cap": m_cap_d.reindex(index).ffill().bfill() if m_cap_d is not None else None}, index=index), \
               pd.DataFrame({"revenue": rev_d.reindex(index).ffill().bfill() if rev_d is not None else None}, index=index), \
               pd.DataFrame({"value": hash_d.reindex(index).ffill().bfill() if hash_d is not None else None}, index=index)
    except Exception as e:
        print(f"[ERROR] Valuation data prep failed: {e}")
        return None, None, None
def _score_technical(weekly, rsi_weekly, idx):
    results = []
    price = weekly["close"].iloc[idx]
    
    # Cyclic Momentum: 21-week EMA
    ema21 = weekly["close"].ewm(span=21).mean().iloc[idx]
    if not np.isnan(ema21):
        rel_ema21 = (price - ema21) / ema21
        # Map: > 20% over -> -10 (Overheated); < 0% (Breakdown) -> -10 (Trend Snapped)
        # Neutral between 0% and 10%
        if rel_ema21 < 0: ema21_score = -10.0 # Breakdown
        elif rel_ema21 > 0.2: ema21_score = -10.0 # Parabolic
        else: ema21_score = 0.0 # Holding support
        results.append(IndicatorResult("EMA21_Weekly", round(ema21_score, 2), True, {"rel_dist": round(rel_ema21, 4)}))
    else:
        results.append(IndicatorResult("EMA21_Weekly", 0.0, False))

    ma200 = weekly["close"].rolling(200, min_periods=13).mean().iloc[idx]
    score_200 = 0.0
    if not np.isnan(ma200):
        dist = (price - ma200) / ma200
        if dist < 0: score_200 = min(10.0, abs(dist) * 50)
        else: score_200 = max(-10.0, -dist * 50)
        results.append(IndicatorResult("200WMA", round(score_200, 2), True))
    else: results.append(IndicatorResult("200WMA", 0.0, False))

    rsi = rsi_weekly.iloc[idx]
    if not np.isnan(rsi):
        rsi_score = (50 - rsi) / 2
        results.append(IndicatorResult("RSI_Weekly", round(max(-10, min(10, rsi_score)), 2), True))
    else: results.append(IndicatorResult("RSI_Weekly", 0.0, False))

    ema26 = weekly["close"].ewm(span=26).mean().iloc[idx]
    stretch_score = 0.0
    if not np.isnan(ema26):
        dist_ema = (price - ema26) / ema26
        if dist_ema > 0.2: stretch_score = -10.0
        elif dist_ema > 0.1: stretch_score = -5.0
        results.append(IndicatorResult("Short_Term_Stretch", round(stretch_score, 2), True))
    else: results.append(IndicatorResult("Short_Term_Stretch", 0.0, False))
    return results

def _score_macro(net_liq, yields, dxy, idx):
    results = []
    if net_liq is not None:
        liq = net_liq.iloc[idx]
        ma_liq = net_liq.rolling(52).mean().iloc[idx]
        if not np.isnan(ma_liq):
            dist = (liq - ma_liq) / ma_liq
            liq_score = min(10.0, max(-10.0, dist * 100))
            results.append(IndicatorResult("Net_Liquidity", round(liq_score, 2), True))
        else: results.append(IndicatorResult("Net_Liquidity", 0.0, False))
    else: results.append(IndicatorResult("Net_Liquidity", 0.0, False))

    if yields is not None:
        y13 = yields.rolling(13).mean().iloc[idx]
        y52 = yields.rolling(52).mean().iloc[idx]
        if not np.isnan(y52):
            dist = (y52 - y13) / y52
            y_score = min(10.0, max(-10.0, dist * 200))
            results.append(IndicatorResult("Yields", round(y_score, 2), True))
        else: results.append(IndicatorResult("Yields", 0.0, False))
    else: results.append(IndicatorResult("Yields", 0.0, False))

    if dxy is not None:
        d13 = dxy.rolling(13).mean().iloc[idx]
        d52 = dxy.rolling(52).mean().iloc[idx]
        if not np.isnan(d52):
            dist = (d52 - d13) / d52
            d_score = min(10.0, max(-10.0, dist * 200))
            results.append(IndicatorResult("DXY_Regime", round(d_score, 2), True))
        else: results.append(IndicatorResult("DXY_Regime", 0.0, False))
    else: results.append(IndicatorResult("DXY_Regime", 0.0, False))
    return results

def _score_valuation(m_cap_df, puell_df, hash_df, weekly, idx):
    """
    Score valuation block using available fundamentals and cyclic proxies.
    """
    results = []
    price = weekly["close"].iloc[idx]
    ma200 = weekly["close"].rolling(200, min_periods=13).mean().iloc[idx]
    
    # 1. MVRV Proxy: Distance from 200WMA (Reliable циклическая floor)
    if not np.isnan(ma200):
        # Scale: Price < MA200 -> Bullish. Price > 2.5*MA200 -> Bearish
        ratio = price / ma200
        if ratio < 1.0: mvrv_score = (1.0 - ratio) * 50 # 0.8 -> 10.0
        else: mvrv_score = (1.0 - ratio) * 5.0 # 3.0 -> -10.0
        results.append(IndicatorResult("MVRV_Proxy", round(max(-10, min(10, mvrv_score)), 2), True))
    else: results.append(IndicatorResult("MVRV_Proxy", 0.0, False))

    # 2. Puell Multiple (Miners Revenue vs 52w MA)
    if puell_df is not None:
        rev = puell_df["revenue"].iloc[idx]
        rev_ma = puell_df["revenue"].rolling(52).mean().iloc[idx]
        if not np.isnan(rev_ma):
            multiple = rev / rev_ma
            if multiple < 1.0: puell_score = (1.0 - multiple) * 20 # 0.5 -> 10.0
            else: puell_score = (1.0 - multiple) * 5.0 # 3.0 -> -10.0
            results.append(IndicatorResult("Puell_Multiple", round(max(-10, min(10, puell_score)), 2), True))
        else: results.append(IndicatorResult("Puell_Multiple", 0.0, False))
    else: results.append(IndicatorResult("Puell_Multiple", 0.0, False))

    # 3. Hash Ribbon (1w vs 8w MA)
    if hash_df is not None:
        fast = hash_df["value"].rolling(30).mean().iloc[idx]
        slow = hash_df["value"].rolling(60).mean().iloc[idx]
        if not np.isnan(slow):
            # Capitulation (fast < slow) is BULLISH for accumulation, 
            # but NEUTRAL for overheating/exits. We return 0.0 to avoid false REDUCE.
            if fast < slow: hash_score = 0.0 
            else: hash_score = 5.0 # Recovery/Growth is generally slightly bullish
            results.append(IndicatorResult("Hash_Ribbon", hash_score, True))
        else: results.append(IndicatorResult("Hash_Ribbon", 0.0, False))
    else: results.append(IndicatorResult("Hash_Ribbon", 0.0, False))
    return results

def _load_btc_daily():
    try:
        df = pd.read_csv("data/btc_daily.csv", index_col=0, parse_dates=True)
        return df, "local_csv"
    except: return None, None

def _to_weekly_ohlcv(df):
    logic = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return df.resample("W").apply(logic)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def _prepare_fng_series(index):
    try:
        import requests
        resp = requests.get("https://api.alternative.me/fng/?limit=5000", timeout=10)
        df = pd.DataFrame(resp.json()["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
        df["value"] = pd.to_numeric(df["value"])
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        return df["value"].reindex(index).ffill().bfill()
    except: return None

def calculate_forward_returns(prices, date, forward_days=[28, 84, 182]):
    results = {}
    try:
        start_price = prices.loc[date]
        for days in forward_days:
            target_date = date + pd.Timedelta(days=days)
            idx = prices.index.get_indexer([target_date], method='nearest')[0]
            if idx >= 0:
                results[f"{days}_day_return"] = (prices.iloc[idx] - start_price) / start_price
            else: results[f"{days}_day_return"] = None
    except:
        for days in forward_days: results[f"{days}_day_return"] = None
    return results
