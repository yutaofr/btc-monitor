import pandas as pd

from src.indicators.base import IndicatorResult
from src.backtest.btc_backtest import _calculate_final_score, _score_valuation, _BacktestTracker
from src.strategy.engine import StrategyEngine


def _result(name, score, *, valid=True, details=None, description="", weight=1.0):
    return IndicatorResult(
        name=name,
        score=score,
        is_valid=valid,
        details=details or {},
        description=description,
        weight=weight,
    )


def test_backtest_score_uses_same_layered_blend_as_live_engine():
    engine = StrategyEngine(tracker=_BacktestTracker())
    results = [
        _result("200WMA", 8.0),
        _result("MVRV_Proxy", 8.0, weight=1.5),
        _result("Puell_Multiple", 8.0, weight=1.2),
        _result("Net_Liquidity", 8.0),
        _result("Yields", 8.0),
        _result("Cycle_Pos", 8.0),
        _result("RSI_Div", -2.0),
        _result("FearGreed", -2.0),
        _result("Options_Wall", 5.0, valid=False, details={"research_only": True}),
    ]

    assert _calculate_final_score(results, engine) == engine.calculate_final_score(results)


def test_score_valuation_emits_live_parity_factor_names():
    weekly_index = pd.to_datetime(["2026-03-20"])
    mvrv_weekly = pd.DataFrame({"price": [100000.0], "ma_730": [20000.0]}, index=weekly_index)
    puell_weekly = pd.DataFrame({"revenue": [5000.0], "ma_365": [1000.0]}, index=weekly_index)

    results = _score_valuation(mvrv_weekly, puell_weekly, 0)
    names = [result.name for result in results]

    assert names == ["MVRV_Proxy", "Puell_Multiple", "Production_Cost"]
    assert results[0].score == -10.0
    assert results[1].score == -10.0
    assert results[2].details["research_only"] is True
