import pytest
import pandas as pd
import os
from src.backtest.advisory_backtest import generate_advisory_backtest

def test_backtest_output_schema(mocker, tmp_path):
    # Mock some basic history data
    mock_history = [
        {"date": "2024-01-01", "price": 40000, "action": "ADD", "confidence": 90, "tactical_state": "CONFIRMED_UP", "strategic_regime": "BULLISH", "score": 85.0}
    ]
    mocker.patch("src.backtest.advisory_backtest.evaluate_history", return_value=pd.DataFrame(mock_history))
    
    mock_prices = pd.Series([40000.0, 48000.0], index=pd.to_datetime(["2024-01-01", "2024-07-01"]))
    mocker.patch("src.backtest.advisory_backtest.fetch_prices", return_value=mock_prices)
    
    results = generate_advisory_backtest()
    df = results["metrics_df"]
    
    # Simulate writing the artifact to disk
    artifact_path = tmp_path / "advisory_backtest_result.csv"
    df.to_csv(artifact_path, index=False)
    
    assert os.path.exists(artifact_path)
    
    # Read back and purely verify schema expectations
    saved_df = pd.read_csv(artifact_path)
    required_columns = ["date", "action", "confidence", "tactical_state", "strategic_regime", "score", "28_day_return", "84_day_return", "182_day_return", "precision"]
    
    for col in required_columns:
        assert col in saved_df.columns, f"Missing required column {col} in serialized artifact."
