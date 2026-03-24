import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.indicators.macro_liquid import MacroIndicator
from unittest.mock import MagicMock

def test_dxy_regime_falling():
    """
    Test DXY falling regime: SMA30 < SMA90 -> Bullish (Score +6.0).
    Note: For simplicity, the current mock-based test will use a smaller window if needed.
    """
    mock_fetcher = MagicMock()
    # Create 100 days of DXY data
    dates = [datetime.now() - timedelta(days=i) for i in range(100)]
    dates.reverse()
    
    # Falling DXY: 100 -> 90
    dxy_values = [100 - (i * 0.1) for i in range(100)]
    mock_fetcher.get_dxy.return_value = pd.Series(dxy_values, index=dates)
    
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_dxy_regime_score()
    
    assert result.name == "DXY_Regime"
    assert result.score > 0
    assert "falling" in result.description

def test_yield_regime_rising():
    """
    Test Yield rising regime: SMA30 > SMA90 -> Bearish (Score -6.0).
    """
    mock_fetcher = MagicMock()
    dates = [datetime.now() - timedelta(days=i) for i in range(100)]
    dates.reverse()
    
    # Rising Yield: 3.0 -> 4.0
    yield_values = [3.0 + (i * 0.01) for i in range(100)]
    mock_fetcher.get_us10y.return_value = pd.Series(yield_values, index=dates)
    
    indicator = MacroIndicator(fetcher=mock_fetcher)
    result = indicator.get_yield_divergence_score()
    
    assert result.name == "Yields"
    assert result.score < 0
    assert "rising" in result.description
