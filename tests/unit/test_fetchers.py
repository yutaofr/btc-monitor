import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.fetchers.fred_fetcher import FredFetcher
from src.fetchers.binance_fetcher import BinanceFetcher

def test_fred_net_liquidity_alignment(mocker):
    fetcher = FredFetcher(api_key="fake")
    
    # Mock return values for FRED series
    dates = pd.to_datetime(['2024-01-03', '2024-01-10', '2024-01-17'])
    walcl_mock = pd.Series([7000, 6900, 6800], index=dates)
    tga_mock = pd.Series([500, 600, 700], index=dates)
    # RRP is daily, mock more dates
    rrp_dates = pd.date_range(start='2024-01-01', end='2024-01-20', freq='D')
    rrp_mock = pd.Series([100] * len(rrp_dates), index=rrp_dates)

    mocker.patch.object(fetcher, 'get_series', side_effect=[walcl_mock, tga_mock, rrp_mock])
    
    df = fetcher.get_net_liquidity()
    assert df is not None
    assert "net_liquidity" in df.columns
    # Check values: 7000 - 500 - 100 = 6400
    assert df["net_liquidity"].iloc[0] == 6400

def test_binance_fetch_ohlcv_error(mocker):
    fetcher = BinanceFetcher()
    mocker.patch.object(fetcher.exchange, 'fetch_ohlcv', side_effect=Exception("API Down"))
    
    df = fetcher.fetch_ohlcv()
    assert df is None

def test_binance_ohlcv_parsing(mocker):
    fetcher = BinanceFetcher()
    mock_ohlcv = [
        [1700000000000, 30000, 31000, 29000, 30500, 1000],
        [1700086400000, 30500, 32000, 30000, 31500, 1100]
    ]
    mocker.patch.object(fetcher.exchange, 'fetch_ohlcv', return_value=mock_ohlcv)
    
    df = fetcher.fetch_ohlcv()
    assert len(df) == 2
    assert df.iloc[0]['close'] == 30500
    assert df.index.name == 'timestamp'
