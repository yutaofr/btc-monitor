import argparse
import os

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from fredapi import Fred
from ccxt import binance as ccxt_binance

from src.config import Config
from src.indicators.base import IndicatorResult, calculate_rsi


def _load_btc_daily(start=None, end=None):
    df = pd.DataFrame()
    source = "yfinance"
    try:
        if start or end:
            df = yf.download("BTC-USD", start=start, end=end, interval="1d", auto_adjust=False, progress=False)
        else:
            df = yf.download("BTC-USD", period="max", interval="1d", auto_adjust=False, progress=False)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        df = _load_btc_daily_coingecko()
        source = "coingecko"

    if df.empty:
        df = _load_btc_daily_cryptocompare()
        source = "cryptocompare"

    if df.empty:
        df = _load_btc_daily_binance()
        source = "binance"

    if df.empty:
        raise RuntimeError("No BTC-USD data returned from data sources.")

    df = df.rename(columns={c: c.lower().replace(" ", "_") for c in df.columns})
    df.index = pd.to_datetime(df.index)

    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    df = df.dropna(subset=["close"])
    return df, source


def _load_btc_daily_coingecko():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "max", "interval": "daily"}
    try:
        resp = requests.get(url, params=params, timeout=20, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            return pd.DataFrame()
        data = resp.json()
    except Exception:
        return pd.DataFrame()

    prices = data.get("prices", [])
    if not prices:
        return pd.DataFrame()

    volumes = data.get("total_volumes", [])
    volume_map = {ts: vol for ts, vol in volumes} if volumes else {}

    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["volume"] = df["timestamp"].map(volume_map)
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.dropna(subset=["price"])
    df = df.set_index("datetime").sort_index()

    df["open"] = df["price"]
    df["high"] = df["price"]
    df["low"] = df["price"]
    df["close"] = df["price"]
    df = df[["open", "high", "low", "close", "volume"]]
    return df


def _load_btc_daily_cryptocompare():
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {"fsym": "BTC", "tsym": "USD", "allData": "true"}
    try:
        resp = requests.get(url, params=params, timeout=20, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            return pd.DataFrame()
        data = resp.json()
    except Exception:
        return pd.DataFrame()

    series = data.get("Data", {}).get("Data", [])
    if not series:
        return pd.DataFrame()

    df = pd.DataFrame(series)
    df["datetime"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("datetime").sort_index()
    df = df.rename(
        columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volumeto": "volume"
        }
    )
    df = df[["open", "high", "low", "close", "volume"]]
    return df


def _load_btc_daily_binance():
    try:
        exchange = ccxt_binance({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe="1d", limit=2000)
    except Exception:
        return pd.DataFrame()

    if not ohlcv:
        return pd.DataFrame()

    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("datetime").sort_index()
    df = df[["open", "high", "low", "close", "volume"]]
    return df


def _to_weekly_ohlcv(daily_df):
    weekly = daily_df.resample("W-FRI").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }
    )
    weekly = weekly.dropna(subset=["open", "close"])
    return weekly


def _load_macro_series():
    if not Config.FRED_API_KEY:
        return None, None
    fred = Fred(api_key=Config.FRED_API_KEY)

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


def _calculate_final_score(results):
    valid_weighted_sum = 0.0
    total_weight = 0.0
    for res in results:
        if not res.is_valid:
            continue
        valid_weighted_sum += res.score * res.weight
        total_weight += res.weight
    if total_weight == 0:
        return np.nan
    return round((valid_weighted_sum / total_weight) * 10, 2)


def _score_technical(weekly, pi_weekly, rsi_weekly, idx):
    results = []

    close = weekly["close"].iloc[idx]
    wma_200 = weekly["close"].rolling(window=200).mean().iloc[idx]
    if pd.isna(wma_200):
        results.append(IndicatorResult("200WMA", 0, description="Insufficient data", is_valid=False))
    else:
        ratio = close / wma_200
        if ratio <= 1.0:
            score = 10.0
        else:
            score = max(-10.0, 10.0 - (ratio - 1.0) * 20.0)
        results.append(
            IndicatorResult(
                name="200WMA",
                score=round(score, 2),
                details={"close": close, "200wma": wma_200, "ratio": ratio},
                description=f"Price is {ratio:.2f}x of 200WMA"
            )
        )

    sma_111 = pi_weekly["sma111"].iloc[idx]
    sma_350_x2 = pi_weekly["sma350x2"].iloc[idx]
    if pd.isna(sma_111) or pd.isna(sma_350_x2):
        results.append(IndicatorResult("Pi_Cycle", 0, description="Insufficient data", is_valid=False))
    else:
        diff_ratio = sma_111 / sma_350_x2
        if diff_ratio >= 1.0:
            score = -10.0
        elif diff_ratio >= 0.9:
            score = -5.0
        else:
            score = 5.0
        results.append(
            IndicatorResult(
                name="Pi_Cycle",
                score=score,
                details={"111dma": sma_111, "350dma_x2": sma_350_x2},
                description="Pi Cycle Top gap is healthy" if score > 0 else "Pi Cycle Top imminent"
            )
        )

    if idx < 5 or pd.isna(rsi_weekly.iloc[idx]) or pd.isna(rsi_weekly.iloc[idx - 5]):
        results.append(IndicatorResult("RSI_Div", 0, description="Insufficient data", is_valid=False))
    else:
        curr_price = weekly["close"].iloc[idx]
        prev_price = weekly["close"].iloc[idx - 5]
        curr_rsi = rsi_weekly.iloc[idx]
        prev_rsi = rsi_weekly.iloc[idx - 5]
        if curr_price < prev_price and curr_rsi > prev_rsi:
            score = 10.0
            desc = "Bullish Weekly RSI Divergence"
        elif curr_price > prev_price and curr_rsi < prev_rsi:
            score = -10.0
            desc = "Bearish Weekly RSI Divergence"
        else:
            score = 0
            desc = "No RSI Divergence"
        results.append(
            IndicatorResult(
                name="RSI_Div",
                score=score,
                details={"curr_rsi": curr_rsi, "prev_rsi": prev_rsi},
                description=desc
            )
        )

    ath = weekly["high"].cummax().iloc[idx]
    drawdown = (weekly["close"].iloc[idx] - ath) / ath
    if drawdown < -0.7:
        score = 10.0
    elif drawdown > -0.1:
        score = -10.0
    else:
        score = ((-drawdown - 0.4) / 0.3) * 10
    results.append(
        IndicatorResult(
            name="Cycle_Pos",
            score=round(score, 2),
            details={"drawdown": round(drawdown, 4), "ath": ath},
            description=f"Market is {abs(drawdown) * 100:.1f}% off from ATH"
        )
    )

    return results


def _score_macro(net_liq, yields, idx):
    results = []
    if net_liq is None or yields is None:
        results.append(IndicatorResult("Net_Liquidity", 0, description="Missing FRED data", is_valid=False))
        results.append(IndicatorResult("Yields", 0, description="Missing FRED data", is_valid=False))
        return results

    curr_liq = net_liq.iloc[idx]
    prev_liq = net_liq.iloc[idx - 1] if idx >= 1 else np.nan
    if pd.isna(curr_liq) or pd.isna(prev_liq) or prev_liq == 0:
        results.append(IndicatorResult("Net_Liquidity", 0, description="Insufficient data", is_valid=False))
    else:
        change_pct = (curr_liq - prev_liq) / prev_liq * 100
        if change_pct > 0.5:
            score = 8.0
        elif change_pct < -0.5:
            score = -8.0
        else:
            score = 2.0
        results.append(
            IndicatorResult(
                name="Net_Liquidity",
                score=score,
                details={"change_pct": round(change_pct, 4), "current": curr_liq},
                description=f"Liquidity is {'expanding' if score > 0 else 'contracting'}"
            )
        )

    curr_yield = yields.iloc[idx]
    prev_yield = yields.iloc[idx - 5] if idx >= 5 else np.nan
    if pd.isna(curr_yield) or pd.isna(prev_yield):
        results.append(IndicatorResult("Yields", 0, description="Insufficient data", is_valid=False))
    else:
        if curr_yield < prev_yield:
            score = 5.0
        elif curr_yield > prev_yield * 1.05:
            score = -5.0
        else:
            score = 0
        results.append(
            IndicatorResult(
                name="Yields",
                score=score,
                details={"current": curr_yield, "prev": prev_yield},
                description=f"Yields are {'falling' if score > 0 else 'rising/stable'}"
            )
        )

    return results


def _score_missing(name, description):
    return IndicatorResult(name, 0, description=description, is_valid=False)


def run_backtest(start=None, end=None, output_dir="data/backtest"):
    daily, data_source = _load_btc_daily(start=start, end=end)
    weekly = _to_weekly_ohlcv(daily)
    weekly["next_open"] = weekly["open"].shift(-1)
    weekly["weekly_return"] = weekly["next_open"] / weekly["open"] - 1

    daily_close = daily["close"]
    pi_daily = pd.DataFrame(
        {
            "sma111": daily_close.rolling(window=111).mean(),
            "sma350x2": daily_close.rolling(window=350).mean() * 2
        }
    )
    pi_weekly = pi_daily.resample("W-FRI").last().reindex(weekly.index).ffill()
    rsi_weekly = calculate_rsi(weekly["close"])

    net_liq, yields = _load_macro_series()
    if net_liq is not None:
        net_liq = net_liq.reindex(weekly.index).ffill()
    if yields is not None:
        yields = yields.reindex(weekly.index).ffill()

    records = []
    desired_position = 0

    for idx, timestamp in enumerate(weekly.index):
        results = []
        results.extend(_score_technical(weekly, pi_weekly, rsi_weekly, idx))
        results.extend(_score_macro(net_liq, yields, idx))
        results.append(_score_missing("FearGreed", "Historical FNG unavailable"))
        results.append(_score_missing("Options_Wall", "Historical options unavailable"))
        results.append(_score_missing("ETF_Flow", "Historical ETF flow unavailable"))

        final_score = _calculate_final_score(results)

        if not np.isnan(final_score):
            if final_score >= Config.THRESHOLD_BUY:
                desired_position = 1
            elif final_score <= Config.THRESHOLD_SELL:
                desired_position = 0

        records.append(
            {
                "date": timestamp,
                "score": final_score,
                "desired_position": desired_position,
                "weekly_open": weekly["open"].iloc[idx],
                "weekly_close": weekly["close"].iloc[idx],
                "weekly_return": weekly["weekly_return"].iloc[idx]
            }
        )

    df = pd.DataFrame(records).set_index("date")
    df["position"] = df["desired_position"].shift(1).fillna(0)
    df = df.dropna(subset=["weekly_return"])
    df["strategy_return"] = df["position"] * df["weekly_return"]
    df["equity"] = (1 + df["strategy_return"]).cumprod()
    df["benchmark_equity"] = (1 + df["weekly_return"]).cumprod()

    metrics = _calculate_metrics(df)
    metrics["data_source"] = data_source

    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "btc_backtest_weekly.csv"))
    pd.DataFrame([metrics]).to_csv(os.path.join(output_dir, "btc_backtest_metrics.csv"), index=False)

    _print_summary(metrics)
    return df, metrics


def _calculate_metrics(df):
    if df.empty:
        return {"error": "No backtest data available."}

    equity = df["equity"]
    benchmark = df["benchmark_equity"]
    total_return = equity.iloc[-1] - 1
    benchmark_return = benchmark.iloc[-1] - 1

    weeks = len(df)
    years = weeks / 52.0
    cagr = (equity.iloc[-1] ** (1 / years) - 1) if years > 0 else np.nan

    weekly_mean = df["strategy_return"].mean()
    weekly_std = df["strategy_return"].std()
    ann_return = weekly_mean * 52
    ann_vol = weekly_std * np.sqrt(52) if weekly_std and weekly_std > 0 else np.nan
    sharpe = ann_return / ann_vol if ann_vol and ann_vol > 0 else np.nan

    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1
    max_drawdown = drawdown.min()
    dd_duration = 0
    max_dd_duration = 0
    for value in drawdown:
        if value < 0:
            dd_duration += 1
        else:
            dd_duration = 0
        max_dd_duration = max(max_dd_duration, dd_duration)

    trades = _calculate_trades(df)
    wins = [t for t in trades if t["return"] > 0]
    win_rate = len(wins) / len(trades) if trades else np.nan
    avg_trade = np.mean([t["return"] for t in trades]) if trades else np.nan

    exposure = df["position"].mean()

    return {
        "total_return": total_return,
        "cagr": cagr,
        "annual_volatility": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "max_drawdown_weeks": max_dd_duration,
        "trades": len(trades),
        "win_rate": win_rate,
        "avg_trade_return": avg_trade,
        "exposure_pct": exposure,
        "benchmark_return": benchmark_return
    }


def _calculate_trades(df):
    trades = []
    position = df["position"].values
    opens = df["weekly_open"].values
    entry_idx = None
    for i in range(1, len(position)):
        if position[i] == 1 and position[i - 1] == 0:
            entry_idx = i
        elif position[i] == 0 and position[i - 1] == 1 and entry_idx is not None:
            trade_return = opens[i] / opens[entry_idx] - 1
            trades.append(
                {
                    "entry": df.index[entry_idx],
                    "exit": df.index[i],
                    "return": trade_return
                }
            )
            entry_idx = None
    return trades


def _print_summary(metrics):
    if "error" in metrics:
        print(metrics["error"])
        return

    def fmt_pct(value):
        return f"{value * 100:.2f}%" if value == value else "n/a"

    def fmt_float(value):
        return f"{value:.2f}" if value == value else "n/a"

    print("BTC Backtest Summary")
    print(f"Data Source: {metrics.get('data_source', 'unknown')}")
    if metrics.get("data_source") == "coingecko":
        print("Note: CoinGecko provides daily close/volume; OHLC is approximated from close.")
    if metrics.get("data_source") == "binance":
        print("Note: Binance history is limited; results may not cover full BTC history.")
    print(f"Total Return: {fmt_pct(metrics['total_return'])}")
    print(f"CAGR: {fmt_pct(metrics['cagr'])}")
    print(f"Annual Volatility: {fmt_pct(metrics['annual_volatility'])}")
    print(f"Sharpe: {fmt_float(metrics['sharpe'])}")
    print(f"Max Drawdown: {fmt_pct(metrics['max_drawdown'])}")
    print(f"Max Drawdown Duration (weeks): {metrics['max_drawdown_weeks']}")
    print(f"Trades: {metrics['trades']}")
    print(f"Win Rate: {fmt_pct(metrics['win_rate'])}")
    print(f"Avg Trade Return: {fmt_pct(metrics['avg_trade_return'])}")
    print(f"Exposure: {fmt_pct(metrics['exposure_pct'])}")
    print(f"Buy & Hold Return: {fmt_pct(metrics['benchmark_return'])}")


def main():
    parser = argparse.ArgumentParser(description="BTC weekly backtest using composite score")
    parser.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default="data/backtest", help="Output directory for CSVs")
    args = parser.parse_args()

    run_backtest(start=args.start, end=args.end, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
