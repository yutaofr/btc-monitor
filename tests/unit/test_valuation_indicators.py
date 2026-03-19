import pytest
from src.indicators.valuation import ValuationIndicator
from src.indicators.base import IndicatorResult
import pandas as pd

@pytest.fixture
def mock_valuation_indicator(mocker):
    # Mock the fetcher
    fetcher = mocker.Mock()
    indicator = ValuationIndicator(fetcher=fetcher)
    return indicator

def test_puell_multiple_extreme_bull(mock_valuation_indicator, mocker):
    # Puell < 0.5 -> Score 10
    rev_data = pd.DataFrame({
        'value': [1000] * 365 + [200] # Current rev 200, average ~1000
    })
    mock_valuation_indicator.fetcher.get_miners_revenue.return_value = rev_data
    
    result = mock_valuation_indicator.get_puell_multiple_score()
    assert result.score == 10.0
    assert "low" in result.description

def test_puell_multiple_neutral(mock_valuation_indicator, mocker):
    # Puell = 1.0 -> Score 2
    rev_data = pd.DataFrame({
        'value': [1000] * 366
    })
    mock_valuation_indicator.fetcher.get_miners_revenue.return_value = rev_data
    
    result = mock_valuation_indicator.get_puell_multiple_score()
    assert result.score == 2.0

def test_mvrv_proxy_bubble(mock_valuation_indicator, mocker):
    # Proxy > 3.7 -> Score -10
    # Price = 100,000, 2yr MA = 20,000 -> Ratio 5.0
    price_data = pd.DataFrame({
        'value': [20000] * 730 + [100000]
    })
    mock_valuation_indicator.fetcher.fetch_chart.return_value = price_data
    
    result = mock_valuation_indicator.get_mvrv_proxy_score()
    assert result.score == -10.0

def test_mvrv_proxy_accumulate(mock_valuation_indicator, mocker):
    # Proxy < 1.0 -> Score ~10
    # Price = 15,000, 2yr MA = 20,000 -> Ratio 0.75
    price_data = pd.DataFrame({
        'value': [20000] * 730 + [15000]
    })
    mock_valuation_indicator.fetcher.fetch_chart.return_value = price_data
    
    result = mock_valuation_indicator.get_mvrv_proxy_score()
    assert result.score == 10.0
