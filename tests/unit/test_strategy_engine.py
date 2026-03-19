import pytest

from src.config import Config
from src.indicators.base import IndicatorResult
from src.strategy.engine import StrategyEngine
from src.strategy.strategic_engine import StrategicEngine
from src.strategy.tactical_engine import TacticalEngine


@pytest.fixture
def mock_engine(mocker):
    engine = StrategyEngine(tracker=mocker.Mock())
    mocker.patch.object(engine.tech, "get_200wma_score")
    mocker.patch.object(engine.tech, "get_pi_cycle_score")
    mocker.patch.object(engine.tech, "get_rsi_divergence_score")
    mocker.patch.object(engine.macro, "get_net_liquidity_score")
    mocker.patch.object(engine.macro, "get_yield_divergence_score")
    mocker.patch.object(engine.sentiment, "get_fear_greed_score")
    mocker.patch.object(engine.sentiment, "get_cycle_position_score")
    mocker.patch.object(engine.opt_etf, "get_options_wall_score")
    mocker.patch.object(engine.opt_etf, "get_etf_flow_divergence_score")
    mocker.patch.object(engine.tech.fetcher, "get_current_price", return_value=50000)
    return engine


def _result(name, score, *, valid=True, details=None, description="", weight=1.0):
    return IndicatorResult(
        name=name,
        score=score,
        is_valid=valid,
        details=details or {},
        description=description,
        weight=weight,
    )


def test_strategic_engine_uses_core_factors_only():
    engine = StrategicEngine()
    results = [
        _result("200WMA", 10.0),
        _result("MVRV_Proxy", 10.0, weight=1.5),
        _result("Puell_Multiple", 10.0, weight=1.2),
        _result("Net_Liquidity", 10.0),
        _result("Yields", 10.0),
        _result("Cycle_Pos", 10.0),
        _result("RSI_Div", -10.0),
        _result("FearGreed", -10.0),
        _result("Production_Cost", 10.0, valid=False, details={"research_only": True}),
    ]

    assert engine.calculate_score(results) == 100.0


def test_tactical_engine_uses_secondary_factors_only():
    engine = TacticalEngine()
    results = [
        _result("RSI_Div", 10.0),
        _result("FearGreed", 10.0),
        _result("200WMA", -10.0),
        _result("MVRV_Proxy", -10.0),
        _result("Options_Wall", 10.0, valid=False, details={"research_only": True}),
    ]

    assert engine.calculate_score(results) == 100.0


def test_strategy_engine_combines_strategic_and_tactical_layers(mocker):
    engine = StrategyEngine(tracker=mocker.Mock())

    strategic_results = [
        _result("200WMA", 8.0),
        _result("MVRV_Proxy", 8.0, weight=1.5),
        _result("Puell_Multiple", 8.0, weight=1.2),
        _result("Net_Liquidity", 8.0),
        _result("Yields", 8.0),
        _result("Cycle_Pos", 8.0),
    ]
    tactical_results = [
        _result("RSI_Div", -2.0),
        _result("FearGreed", -2.0),
    ]
    research_results = [
        _result("Production_Cost", 10.0, valid=False, details={"research_only": True}),
    ]
    all_results = strategic_results + tactical_results + research_results

    strategic_score = engine.strategic_engine.calculate_score(all_results)
    tactical_score = engine.tactical_engine.calculate_score(all_results)

    assert strategic_score == 80.0
    assert tactical_score == -20.0
    assert engine.calculate_final_score(all_results) == 50.0


def test_strategy_engine_does_not_penalize_missing_tactical_layer(mocker):
    engine = StrategyEngine(tracker=mocker.Mock())
    strategic_only_results = [
        _result("200WMA", 10.0),
        _result("MVRV_Proxy", 10.0, weight=1.5),
        _result("Puell_Multiple", 10.0, weight=1.2),
        _result("Net_Liquidity", 10.0),
        _result("Yields", 10.0),
        _result("Cycle_Pos", 10.0),
    ]

    assert engine.calculate_final_score(strategic_only_results) == 100.0


def test_strategy_engine_returns_neutral_when_strategic_layer_missing(mocker):
    engine = StrategyEngine(tracker=mocker.Mock())
    tactical_only_results = [
        _result("RSI_Div", 10.0),
        _result("FearGreed", 10.0),
    ]

    assert engine.calculate_final_score(tactical_only_results) == 0.0


def test_research_factors_are_excluded_from_production_score(mock_engine):
    results = [
        _result("200WMA", 0.0),
        _result("Pi_Cycle", 0.0),
        _result("RSI_Div", 0.0),
        _result("Net_Liquidity", 0.0),
        _result("Yields", 0.0),
        _result("FearGreed", 0.0),
        _result("Cycle_Pos", 0.0),
        _result("MVRV_Proxy", 0.0, weight=1.5),
        _result("Puell_Multiple", 0.0, weight=1.2),
        _result("Production_Cost", 10.0, valid=False, details={"research_only": True}),
        _result("Options_Wall", 10.0, valid=False, details={"research_only": True}),
        _result("ETF_Flow", 10.0, valid=False, details={"research_only": True}),
    ]

    assert mock_engine.calculate_final_score(results) == 0.0


def test_research_factors_are_reported_as_research_only(mock_engine):
    mock_engine.tracker.state = {"current_month": "2026-03", "accumulated_budget_multiplier": 1.0}
    results = [
        _result("200WMA", 0.0),
        _result("Pi_Cycle", 0.0),
        _result("RSI_Div", 0.0),
        _result("Net_Liquidity", 0.0),
        _result("Yields", 0.0),
        _result("FearGreed", 0.0),
        _result("Cycle_Pos", 0.0),
        _result("MVRV_Proxy", 0.0, weight=1.5),
        _result("Puell_Multiple", 0.0, weight=1.2),
        _result(
            "Production_Cost",
            10.0,
            valid=False,
            details={"research_only": True},
            description="Research-only: network fundamental floor placeholder",
        ),
        _result(
            "Options_Wall",
            10.0,
            valid=False,
            details={"research_only": True},
            description="Research-only: BTC options wall",
        ),
        _result(
            "ETF_Flow",
            10.0,
            valid=False,
            details={"research_only": True},
            description="Research-only: ETF flow divergence",
        ),
    ]
    report = mock_engine._generate_report(results, 0.0, 50000, strategic_score=0.0, tactical_score=0.0)

    assert "🔒 **Production_Cost** (research-only)" in report
    assert "🔒 **Options_Wall** (research-only)" in report
    assert "🔒 **ETF_Flow** (research-only)" in report
    assert "Strategic Score" in report
    assert "Tactical Score" in report


def test_unknown_factors_are_reported_as_excluded(mock_engine):
    mock_engine.tracker.state = {"current_month": "2026-03", "accumulated_budget_multiplier": 1.0}
    results = [
        _result("Pi_Cycle", -5.0, description="Pi Cycle Top imminent"),
    ]

    report = mock_engine._generate_report(results, 0.0, 50000, strategic_score=0.0, tactical_score=0.0)

    assert "**Pi_Cycle** (excluded)" in report


def test_report_includes_coverage_and_missing_core_factors(mock_engine):
    mock_engine.tracker.state = {"current_month": "2026-03", "accumulated_budget_multiplier": 1.0}
    results = [
        _result("200WMA", 10.0),
        _result("MVRV_Proxy", 10.0, weight=1.5),
        _result("RSI_Div", 5.0),
        _result("FearGreed", 5.0),
        _result(
            "Options_Wall",
            5.0,
            valid=False,
            details={"research_only": True},
            description="Research-only: BTC options wall",
        ),
    ]

    report = mock_engine._generate_report(results, 85.0, 50000, strategic_score=100.0, tactical_score=50.0)

    assert "Strategic Coverage" in report
    assert "Missing Required Core Factors" in report
    assert "Puell_Multiple" in report
    assert "Net_Liquidity" in report
    assert "Excluded Research Factors" in report
    assert "Options_Wall" in report


def test_strategy_cycle_buy_trigger(mock_engine, mocker):
    results = [
        _result("200WMA", 10.0),
        _result("MVRV_Proxy", 10.0, weight=1.5),
        _result("Puell_Multiple", 10.0, weight=1.2),
        _result("Net_Liquidity", 10.0),
        _result("Yields", 10.0),
        _result("Cycle_Pos", 10.0),
        _result("RSI_Div", 10.0),
        _result("FearGreed", 10.0),
    ]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {
        "has_bought_this_month": False,
        "monthly_action_count": 0,
        "accumulated_budget_multiplier": 2.0,
        "current_month": "2026-03",
    }

    decision, report = mock_engine.run_strategy_cycle()

    assert decision == "BUY"
    assert "2.0x budget" in report
    mock_engine.tracker.record_action.assert_called_with(
        "BUY",
        100.0,
        50000,
        budget_multiplier_used=2.0,
        metadata={"regime": "AGGRESSIVE_ACCUMULATE", "timing": "BUY_NOW"},
    )


def test_strategy_cycle_partial_buy_trigger(mock_engine, mocker):
    results = [
        _result("200WMA", 6.0),
        _result("MVRV_Proxy", 6.0, weight=1.5),
        _result("Puell_Multiple", 6.0, weight=1.2),
        _result("Net_Liquidity", 6.0),
        _result("Yields", 6.0),
        _result("Cycle_Pos", 6.0),
        _result("RSI_Div", 5.0),
        _result("FearGreed", 5.0),
    ]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {
        "has_bought_this_month": False,
        "monthly_action_count": 0,
        "accumulated_budget_multiplier": 2.0,
        "current_month": "2026-03",
    }

    decision, report = mock_engine.run_strategy_cycle()

    assert decision == "PARTIAL_BUY"
    assert "0.5x budget" in report
    mock_engine.tracker.record_action.assert_called_with(
        "PARTIAL_BUY",
        57.0,
        50000,
        budget_multiplier_used=0.5,
        metadata={"regime": "NORMAL_ACCUMULATE", "timing": "STAGGER_BUY"},
    )


def test_strategy_cycle_wait_when_already_acted(mock_engine, mocker):
    results = [
        _result("200WMA", 10.0),
        _result("MVRV_Proxy", 10.0, weight=1.5),
        _result("Puell_Multiple", 10.0, weight=1.2),
        _result("Net_Liquidity", 10.0),
        _result("Yields", 10.0),
        _result("Cycle_Pos", 10.0),
        _result("RSI_Div", 10.0),
        _result("FearGreed", 10.0),
    ]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {
        "has_bought_this_month": True,
        "monthly_action_count": 1,
        "accumulated_budget_multiplier": 1.0,
        "current_month": "2026-03",
    }

    decision, report = mock_engine.run_strategy_cycle()

    assert decision == "WAIT (Already Acted)"
    assert "already executed this month" in report.lower()


def test_strategy_cycle_alert_trigger(mock_engine, mocker):
    results = [
        _result("200WMA", 2.0),
        _result("MVRV_Proxy", 2.0, weight=1.5),
        _result("Puell_Multiple", 2.0, weight=1.2),
        _result("Net_Liquidity", 2.0),
        _result("Yields", 2.0),
        _result("Cycle_Pos", 2.0),
        _result("RSI_Div", -10.0),
        _result("FearGreed", -10.0),
    ]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {
        "has_bought_this_month": False,
        "monthly_action_count": 0,
        "accumulated_budget_multiplier": 1.0,
        "current_month": "2026-03",
    }

    decision, report = mock_engine.run_strategy_cycle()

    assert decision == "ALERT"
    assert "portfolio risk high" in report.lower()
    mock_engine.tracker.record_action.assert_called_with(
        "ALERT",
        -16.0,
        50000,
        budget_multiplier_used=0.0,
        metadata={"regime": "RISK_REDUCE", "timing": "WAIT"},
    )
