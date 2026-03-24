import pytest
import pandas as pd
import numpy as np
from src.indicators.macro_liquid import MacroIndicator
from src.fetchers.fred_fetcher import FredFetcher

def test_net_liquidity_expansion(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    # Net Liquidity needs 180 days for 180d SMA
    base = 6000.0
    dates = pd.date_range('2024-01-01', periods=200)
    data = pd.DataFrame({
        "net_liquidity": [base] * 199 + [base * 1.05] # Significant jump at the end
    }, index=dates)
    
    mock_fetcher.get_net_liquidity.return_value = data
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_net_liquidity_score()
    
    assert result.score > 0.0
    assert result.is_valid

def test_yields_falling(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    # Yields regime: 30d SMA vs 90d SMA
    dates = pd.date_range('2024-01-01', periods=100)
    # Create falling trend: 5.0 down to 4.0
    yields = pd.Series(np.linspace(5.0, 4.0, 100), index=dates)
    
    mock_fetcher.get_us10y.return_value = yields
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_yield_divergence_score()
    
    assert result.score > 0.0 # Falling yields are bullish (positive score)
    assert result.is_valid

def test_dxy_regime_falling(mocker):
    mock_fetcher = mocker.Mock(spec=FredFetcher)
    dates = pd.date_range('2024-01-01', periods=100)
    # DXY falling: 105 down to 100
    dxy = pd.Series(np.linspace(105.0, 100.0, 100), index=dates)
    
    mock_fetcher.get_dxy.return_value = dxy
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_dxy_regime_score()
    
    assert result.score > 0.0 # Falling DXY is bullish
    assert result.is_valid
