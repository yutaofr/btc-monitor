import pytest
import pandas as pd
import numpy as np
import os
from src.backtest.advisory_backtest import generate_advisory_backtest

def test_backtest_report_generation(mocker, tmp_path):
    """Verify that the backtest generates the expected artifacts."""
    # Mock data dependencies to avoid hitting APIs or real files
    dates = pd.date_range('2024-01-01', periods=20)
    mock_daily = pd.DataFrame({
        "open": [40000]*20, "high": [41000]*20, "low": [39000]*20, "close": [40000]*20, "volume": [1000]*20
    }, index=dates)
    
    mocker.patch("src.backtest.advisory_backtest._load_btc_daily", return_value=(mock_daily, "mock"))
    mocker.patch("src.backtest.advisory_backtest._load_macro_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_valuation_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_fng_series", return_value=None)
    
    # Run the backtest
    generate_advisory_backtest()
    
    assert os.path.exists("data/backtest/advisory_backtest_result.csv")
    assert os.path.exists("data/backtest/advisory_performance_report.md")
