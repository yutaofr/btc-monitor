import pytest
import pandas as pd
from src.indicators.options_etf import OptionsETFIndicator
from src.fetchers.binance_fetcher import BinanceFetcher

def test_options_wall_support(mocker):
    # Mock yfinance Ticker
    mock_ticker = mocker.Mock()
    mocker.patch('yfinance.Ticker', return_value=mock_ticker)
    
    mock_ticker.options = ['2024-01-20']
    mock_opt = mocker.Mock()
    mock_ticker.option_chain.return_value = mock_opt
    mock_opt.puts = pd.DataFrame({
        'strike': [10, 20, 30],
        'openInterest': [100, 500, 200]
    })
    mock_ticker.fast_info = {'lastPrice': 21.0}
    
    indicator = OptionsETFIndicator()
    result = indicator.get_options_wall_score()
    
    # Strike 20 has max OI. Current price 21. Ratio (21-20)/20 = 0.05.
    assert result.score == 5.0
    assert "support" in result.description

def test_etf_flow_divergence_accumulation(mocker):
    mock_binance = mocker.Mock(spec=BinanceFetcher)
    # Price down from 100 to 95 (< 0.97)
    df_btc = pd.DataFrame({'close': [100, 100, 100, 95]}, index=pd.date_range('2024-01-01', periods=4))
    mock_binance.fetch_ohlcv.return_value = df_btc
    
    # Volume spike: avg 100, current 150 (> 1.3)
    df_etf = pd.DataFrame({'Volume': [100, 100, 100, 100, 150]}, index=pd.date_range('2024-01-01', periods=5))
    mocker.patch('yfinance.download', return_value=df_etf)
    
    indicator = OptionsETFIndicator(binance_fetcher=mock_binance)
    result = indicator.get_etf_flow_divergence_score()
    
    assert result.score == 10.0
    assert "Accumulation" in result.description
