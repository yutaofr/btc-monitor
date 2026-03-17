import pytest
import pandas as pd
from src.indicators.macro_liquid import MacroIndicator
from src.fetchers.fred_fetcher import FredFetcher

def test_net_liquidity_expansion(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    # Mock expansion: from 6000 to 6100 (> 0.5%)
    data = pd.DataFrame({
        "net_liquidity": [6000.0, 6100.0]
    }, index=pd.to_datetime(['2024-01-01', '2024-01-08']))
    
    mock_fetcher.get_net_liquidity.return_value = data
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_net_liquidity_score()
    
    assert result.score == 8.0
    assert "expanding" in result.description

def test_net_liquidity_contraction(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    # Mock contraction: from 6100 to 6000 (< -0.5%)
    data = pd.DataFrame({
        "net_liquidity": [6100.0, 6000.0]
    }, index=pd.to_datetime(['2024-01-01', '2024-01-08']))
    
    mock_fetcher.get_net_liquidity.return_value = data
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_net_liquidity_score()
    
    assert result.score == -8.0

def test_yields_falling(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    # Falling yields: 4.5 -> 4.3
    yields = pd.Series([4.5, 4.4, 4.3, 4.2, 4.1], index=pd.date_range('2024-01-01', periods=5))
    
    mock_fetcher.get_us10y.return_value = yields
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_yield_divergence_score()
    
    assert result.score == 5.0
