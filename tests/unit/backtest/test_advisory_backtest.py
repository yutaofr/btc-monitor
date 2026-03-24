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
    
    # Run the backtest to a temporary directory
    generate_advisory_backtest(output_dir=str(tmp_path))
    
    assert os.path.exists(os.path.join(str(tmp_path), "advisory_backtest_result.csv"))
    assert os.path.exists(os.path.join(str(tmp_path), "advisory_performance_report.md"))

def test_production_artifacts_untouched(mocker, tmp_path):
    """Ensure generate_advisory_backtest does not overwrite production artifacts when output_dir is provided."""
    dates = pd.date_range('2024-01-01', periods=5)
    mock_daily = pd.DataFrame({
        "open": [40000]*5, "high": [41000]*5, "low": [39000]*5, "close": [40000]*5, "volume": [1000]*5
    }, index=dates)
    mocker.patch("src.backtest.advisory_backtest._load_btc_daily", return_value=(mock_daily, "mock"))
    mocker.patch("src.backtest.advisory_backtest._load_macro_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_valuation_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_fng_series", return_value=None)
    
    # Spy on DataFrame.to_csv and open to see where they write
    spy_csv = mocker.spy(pd.DataFrame, "to_csv")
    spy_open = mocker.spy(os, "makedirs")

    generate_advisory_backtest(output_dir=str(tmp_path))
    
    # Verify no writes were made to data/backtest
    for call in spy_csv.call_args_list:
        path_arg = str(call[0][1]) if len(call[0]) > 1 else str(call.kwargs.get("path_or_buf", ""))
        assert "data/backtest" not in path_arg, f"Attempted to write to production path: {path_arg}"

def test_sample_counts_and_inadequate_label(mocker, tmp_path):
    dates = pd.date_range('2024-01-01', periods=5)
    mock_daily = pd.DataFrame({
        "open": [40000]*5, "high": [41000]*5, "low": [39000]*5, "close": [40000]*5, "volume": [1000]*5
    }, index=dates)
    mocker.patch("src.backtest.advisory_backtest._load_btc_daily", return_value=(mock_daily, "mock"))
    mocker.patch("src.backtest.advisory_backtest._load_macro_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_valuation_series", return_value=(None, None, None))
    mocker.patch("src.backtest.advisory_backtest._prepare_fng_series", return_value=None)
    
    opts = set(pd.options.mode.chained_assignment) if hasattr(pd.options.mode, 'chained_assignment') else None
    generate_advisory_backtest(output_dir=str(tmp_path))
    
    report_path = os.path.join(str(tmp_path), "advisory_performance_report.md")
    with open(report_path, "r") as f:
        content = f.read()
    
    assert "Inadequate Sample" in content
    assert "(N=" in content
    assert "False Positive Analysis" in content
