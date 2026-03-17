import pytest
import pandas as pd
import numpy as np
from src.indicators.technical import TechnicalIndicator
from src.fetchers.binance_fetcher import BinanceFetcher

def test_200wma_score_undervalued(mocker):
    mock_fetcher = mocker.Mock(spec=BinanceFetcher)
    # Mock index -2 as 30000, 200WMA as 35000 (undervalued)
    data = {'close': [35000] * 210}
    df = pd.DataFrame(data)
    df.iloc[-2, 0] = 30000 
    
    mock_fetcher.fetch_ohlcv.return_value = df
    indicator = TechnicalIndicator(fetcher=mock_fetcher)
    result = indicator.get_200wma_score()
    
    assert result.score == pytest.approx(10.0, abs=0.1)

def test_200wma_score_overvalued(mocker):
    mock_fetcher = mocker.Mock(spec=BinanceFetcher)
    # confirmed close at 60000, 200WMA at 30000 -> ratio 2.0
    data = {'close': [30000] * 210}
    df = pd.DataFrame(data)
    df.iloc[-2, 0] = 60000
    
    mock_fetcher.fetch_ohlcv.return_value = df
    indicator = TechnicalIndicator(fetcher=mock_fetcher)
    result = indicator.get_200wma_score()
    
    assert result.score == pytest.approx(-10.0, abs=0.5)

def test_pi_cycle_top_trigger(mocker):
    mock_fetcher = mocker.Mock(spec=BinanceFetcher)
    data = {'close': [10000] * 750}
    df = pd.DataFrame(data)
    df.iloc[-111:, 0] = 100000 
    
    mock_fetcher.fetch_ohlcv.return_value = df
    indicator = TechnicalIndicator(fetcher=mock_fetcher)
    result = indicator.get_pi_cycle_score()
    
    assert result.score == -10.0
