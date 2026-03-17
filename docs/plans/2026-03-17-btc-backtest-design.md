# BTC Backtest Design

## Goal
Add a weekly BTC backtest to validate the composite score logic using the full historical range. The backtest should be reproducible, avoid lookahead bias, and report full performance metrics.

## Data Sources
- **BTC price history**: `yfinance` (`BTC-USD`) daily OHLCV, resampled to weekly bars. If Yahoo blocks access, fall back to CoinGecko (daily close/volume, OHLC approximated) or CryptoCompare daily OHLC. If both fail, use Binance daily history as last resort.
- **Macro series**: FRED (WALCL, WTREGEN, RRPONTSYD, DGS10) if `FRED_API_KEY` is set.

## Indicator Coverage
Reuse the current composite logic, but only indicators that can be computed from historical data:
- **Technical**: 200WMA, Pi Cycle, RSI divergence, Cycle Position.
- **Macro**: Net Liquidity, US10Y yields (if FRED key available).
- **Dropped (invalid)**: Fear & Greed, Options Wall, ETF Flow (no reliable historical public endpoints).
Invalid indicators are excluded from the weighted normalization.

## Signal Timing
Compute signals at each weekly close (Friday). Trades are executed at the **next week’s open** to avoid same-bar lookahead.

## Strategy Rules
Simple long/flat:
- Enter long when score >= `THRESHOLD_BUY`.
- Exit to flat when score <= `THRESHOLD_SELL`.
- Otherwise carry forward the prior position.

## Metrics and Outputs
Report total return, CAGR, annualized volatility, Sharpe, max drawdown and duration, trade count, win rate, average trade return, exposure, and buy-and-hold return. Write CSV outputs for weekly scores and metrics to `data/backtest/`.
