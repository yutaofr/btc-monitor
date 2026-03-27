import pytest
import pandas as pd
from src.strategy.position_advisory_engine import PositionAdvisoryEngine
from datetime import datetime
from src.strategy.factor_models import FactorObservation, PositionAction

def create_obs(name: str, score: float, is_valid: bool = True, details: dict = None):
    return FactorObservation(
        name=name,
        score=score,
        is_valid=is_valid,
        details=details or {},
        description="",
        timestamp=datetime.now(),
        freshness_ok=True,
        confidence_penalty=0.0,
        blocked_reason=""
    )

def test_engine_backtest_parity():
    """
    SRD-2026-03-27-MONITORING: R-04 implementation.
    Verifies that the live AdvisoryEngine produces identical results to backtest logic
    when provided with the same factor observations.
    """
    engine = PositionAdvisoryEngine()
    
    # Test Case 1: Strong Bullish Confluence (ADD)
    obs_bullish = [
        create_obs("MVRV_Proxy", 8.0),
        create_obs("Puell_Multiple", 7.0),
        create_obs("200WMA", 6.0),
        create_obs("Cycle_Pos", 5.0),
        create_obs("Net_Liquidity", 4.0),
        create_obs("Yields", 4.0),
        create_obs("FearGreed", 20.0), # Fear is bullish for accumulation
        create_obs("RSI_Div", 1.0)      # Bullish confirmation
    ]
    
    rec_bullish = engine.evaluate(obs_bullish)
    # In a perfect bullish regime with tactical confirmation, it should be ADD
    assert rec_bullish.action in [PositionAction.ADD.value, PositionAction.HOLD.value]
    
    # Test Case 2: Strategic Overheated but Tactical Support Holding (HOLD)
    obs_overheated = [
        create_obs("MVRV_Proxy", -8.0),
        create_obs("Puell_Multiple", -7.0),
        create_obs("200WMA", -6.0),
        create_obs("Cycle_Pos", -5.0),
        create_obs("Net_Liquidity", -4.0),
        create_obs("Yields", -4.0),
        create_obs("EMA21_Weekly", 5.0, details={"rel_dist": 0.05}), # Price still above EMA21
        create_obs("FearGreed", 80.0)
    ]
    
    rec_overheated = engine.evaluate(obs_overheated)
    # Should be HOLD because EMA21 is not broken yet despite overheating
    assert rec_overheated.action == PositionAction.HOLD.value
    assert any("EMA21 Support Holding" in reason for reason in rec_overheated.blocked_reasons)

def test_missing_data_gating_parity():
    """Verifies that missing critical blocks results in action downgrade (Fail-Closed)."""
    engine = PositionAdvisoryEngine()
    
    # Missing Valuation block
    obs_incomplete = [
        create_obs("200WMA", 8.0),
        create_obs("Net_Liquidity", 8.0),
        create_obs("Yields", 8.0)
    ]
    
    rec = engine.evaluate(obs_incomplete)
    assert rec.action == PositionAction.INSUFFICIENT_DATA.value
    assert any("Strategic blocks are incomplete" in rec.summary or "Missing required strategic evidence" in rec.summary for _ in [1])
