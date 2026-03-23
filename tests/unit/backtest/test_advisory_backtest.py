import pytest
import pandas as pd
from src.backtest.advisory_backtest import generate_advisory_backtest

def test_advisory_backtest_schema(mocker):
    # Mock some basic history data
    mock_history = [
        {
            "date": "2024-01-01",
            "price": 40000,
            "action": "ADD",
            "confidence": 90,
            "tactical_state": "CONFIRMED_UP",
            "strategic_regime": "BULLISH",
            "score": 85.0
        },
        {
            "date": "2024-01-08",
            "price": 42000,
            "action": "HOLD",
            "confidence": 60,
            "tactical_state": "NEUTRAL",
            "strategic_regime": "BULLISH",
            "score": 60.0
        }
    ]
    
    # We will mock the strategy engine evaluation and just pass history
    mocker.patch("src.backtest.advisory_backtest.evaluate_history", return_value=pd.DataFrame(mock_history))
    
    # Fetcher returning prices
    mock_prices = pd.Series([40000.0, 42000.0, 45000.0, 48000.0], index=pd.to_datetime(["2024-01-01", "2024-01-08", "2024-02-01", "2024-07-01"]))
    mocker.patch("src.backtest.advisory_backtest.fetch_prices", return_value=mock_prices)
    
    results = generate_advisory_backtest()
    
    assert "precision_metrics" in results
    assert "confidence_buckets" in results
    assert "metrics_df" in results
    
    df = results["metrics_df"]
    # Check that forward return columns are added (4wk=28d, 12wk=84d, 26wk=182d)
    assert "28_day_return" in df.columns
    assert "84_day_return" in df.columns
    assert "182_day_return" in df.columns
    assert "precision" in df.columns
