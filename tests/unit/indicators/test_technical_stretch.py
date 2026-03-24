import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.indicators.technical import TechnicalIndicator
from unittest.mock import MagicMock

def test_stretch_overheated():
    """
    Test short-term stretch: Price > 1.25 * EMA182 -> Overheated (-8.0).
    """
    mock_fetcher = MagicMock()
    # Create 200 days of price data
    dates = [datetime.now() - timedelta(days=i) for i in range(200)]
    dates.reverse()
    
    # Flat 1000 for 199 days, then surge to 2000
    prices = [1000] * 199 + [2000]
    mock_fetcher.fetch_ohlcv.return_value = pd.DataFrame({"close": prices}, index=dates)
    
    indicator = TechnicalIndicator(fetcher=mock_fetcher)
    result = indicator.get_short_term_stretch_score()
    
    assert result.name == "Short_Term_Stretch"
    assert result.score == -8.0
    assert result.details["ratio"] > 1.25

def test_stretch_bullish():
    """
    Test short-term stretch: Price < 0.8 * EMA182 -> Bullish (+8.0).
    """
    mock_fetcher = MagicMock()
    dates = [datetime.now() - timedelta(days=i) for i in range(200)]
    dates.reverse()
    
    # Flat 1000 for 199 days, then crash to 500
    prices = [1000] * 199 + [500]
    mock_fetcher.fetch_ohlcv.return_value = pd.DataFrame({"close": prices}, index=dates)
    
    indicator = TechnicalIndicator(fetcher=mock_fetcher)
    result = indicator.get_short_term_stretch_score()
    
    assert result.name == "Short_Term_Stretch"
    assert result.score == 8.0
    assert result.details["ratio"] < 0.8
