import pytest
from src.strategy.engine import StrategyEngine
from src.indicators.base import IndicatorResult
from src.config import Config

@pytest.fixture
def mock_engine(mocker):
    engine = StrategyEngine(tracker=mocker.Mock())
    # Mock all indicator methods
    mocker.patch.object(engine.tech, 'get_200wma_score')
    mocker.patch.object(engine.tech, 'get_pi_cycle_score')
    mocker.patch.object(engine.tech, 'get_rsi_divergence_score')
    mocker.patch.object(engine.macro, 'get_net_liquidity_score')
    mocker.patch.object(engine.macro, 'get_yield_divergence_score')
    mocker.patch.object(engine.sentiment, 'get_fear_greed_score')
    mocker.patch.object(engine.sentiment, 'get_cycle_position_score')
    mocker.patch.object(engine.opt_etf, 'get_options_wall_score')
    mocker.patch.object(engine.opt_etf, 'get_etf_flow_divergence_score')
    mocker.patch.object(engine.tech.fetcher, 'get_current_price', return_value=50000)
    return engine

def test_calculate_final_score_perfect_bull(mock_engine, mocker):
    # All indicators return +10
    results = [IndicatorResult("test", 10.0) for _ in range(9)]
    score = mock_engine.calculate_final_score(results)
    assert score == 100.0

def test_calculate_final_score_missing_data(mock_engine, mocker):
    # 8 indicators return +10, 1 returns Fetch Error
    results = [IndicatorResult(f"test_{i}", 10.0) for i in range(8)]
    results.append(IndicatorResult("fail", 0, description="Fetch error"))
    
    score = mock_engine.calculate_final_score(results)
    # Normalized: (8 * 10) / 8 * 10 = 100.
    assert score == 100.0

def test_strategy_cycle_buy_trigger(mock_engine, mocker):
    # Total score 70 (> THRESHOLD_BUY=60)
    results = [IndicatorResult("test", 7.0) for _ in range(9)]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {"has_bought_this_month": False, "accumulated_budget_multiplier": 2.0, "current_month": "2026-03"}
    
    decision, report = mock_engine.run_strategy_cycle()
    
    assert decision == "BUY"
    assert "2.0x budget" in report
    mock_engine.tracker.record_action.assert_called_with("BUY", 70.0, 50000)

def test_strategy_cycle_already_bought(mock_engine, mocker):
    results = [IndicatorResult("test", 8.0) for _ in range(9)]
    mock_engine.evaluate = mocker.Mock(return_value=results)
    mock_engine.tracker.state = {"has_bought_this_month": True, "accumulated_budget_multiplier": 1.0, "current_month": "2026-03"}
    
    decision, report = mock_engine.run_strategy_cycle()
    
    assert "WAIT (Already Bought)" in decision
    assert "SIGNAL: [BUY]" in report
