import pandas as pd
from src.backtest.generate_dual_report import generate_report


def test_generate_dual_report_includes_stagger_timing_section(tmp_path):
    pos_csv = tmp_path / "position.csv"
    cash_csv = tmp_path / "cash.csv"
    report_path = tmp_path / "dual_report.md"

    pd.DataFrame(
        [
            {"timestamp": "2024-01-01", "action": "ADD", "precision_28": True, "precision_84": True, "precision_182": True},
            {"timestamp": "2024-01-08", "action": "REDUCE", "precision_28": False, "precision_84": False, "precision_182": False},
        ]
    ).to_csv(pos_csv, index=False)

    pd.DataFrame(
        [
            {
                "action": "BUY_NOW",
                "precision_28": True,
                "precision_84": True,
                "precision_182": True,
                "rel_dca_perf_28": 2.0,
                "rel_dca_perf_84": 1.0,
                "timing_success_28": True,
                "timing_success_84": True,
            },
            {
                "action": "STAGGER_BUY",
                "precision_28": None,
                "precision_84": None,
                "precision_182": None,
                "rel_dca_perf_28": -1.5,
                "rel_dca_perf_84": -0.5,
                "timing_success_28": True,
                "timing_success_84": True,
            },
        ]
    ).to_csv(cash_csv, index=False)

    generate_report(str(pos_csv), str(cash_csv), str(report_path))
    content = report_path.read_text()

    assert "#### STAGGER_BUY (DCA beats immediate buy)" in content
    assert "| 28d | -1.50% | 1 | 100.0% |" in content
