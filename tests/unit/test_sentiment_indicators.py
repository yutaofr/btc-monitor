import pytest
import pandas as pd
from src.indicators.sentiment_cycle import SentimentCycleIndicator
from src.fetchers.binance_fetcher import BinanceFetcher

def test_fear_greed_score(mocker):
    indicator = SentimentCycleIndicator()
    
    # Mock requests.get for Fear & Greed
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "data": [{"value": "10", "value_classification": "Extreme Fear"}]
    }
    mocker.patch('requests.get', return_value=mock_resp)
    
    result = indicator.get_fear_greed_score()
    # (50 - 10) / 5 = 8.0
    assert result.score == 8.0
    assert "Extreme Fear" in result.description

def test_cycle_position_deep_bear(mocker):
    mock_fetcher = mocker.Mock(spec=BinanceFetcher)
    # ATH = 100000, current = 25000 -> Drawdown -75%
    data = {'high': [100000] * 250, 'close': [30000] * 250}
    df = pd.DataFrame(data)
    df.iloc[-2, 1] = 25000 # current close
    
    mock_fetcher.fetch_ohlcv.return_value = df
    indicator = SentimentCycleIndicator(fetcher=mock_fetcher)
    result = indicator.get_cycle_position_score()
    
    assert result.score == 10.0
    assert "75.0%" in result.description

def test_cycle_position_overheated(mocker):
    mock_fetcher = mocker.Mock(spec=BinanceFetcher)
    # ATH = 100000, current = 95000 -> Drawdown -5%
    data = {'high': [100000] * 250, 'close': [80000] * 250}
    df = pd.DataFrame(data)
    df.iloc[-2, 1] = 95000
    
    mock_fetcher.fetch_ohlcv.return_value = df
    indicator = SentimentCycleIndicator(fetcher=mock_fetcher)
    result = indicator.get_cycle_position_score()
    
    assert result.score == -10.0
