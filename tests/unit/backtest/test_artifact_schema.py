import pytest
import os

def test_backtest_output_schema():
    """Verify that the generated report has the correct high-confidence sections."""
    report_path = "data/backtest/advisory_performance_report.md"
    if not os.path.exists(report_path):
        pytest.skip("Report not generated yet")
        
    with open(report_path, "r") as f:
        content = f.read()
        
    assert "# High-Confidence Advisory Performance Report" in content
    assert "## 1. Action Distribution" in content
    assert "## 2. Multi-Horizon Precision" in content
    assert "## 3. Regime Breakdown" in content
