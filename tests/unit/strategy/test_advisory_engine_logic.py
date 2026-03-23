import pytest
from datetime import datetime
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation, Action
from src.strategy.strategic_engine import StrategicRegime

def create_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name, score=score, is_valid=is_valid, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_missing_required_blocks_returns_insufficient_data():
    """Ensure missing strategic blocks results in INSUFFICIENT_DATA."""
    engine = AdvisoryEngine()
    
    # Missing all blocks
    obs = []
    rec = engine.evaluate(obs)
    
    assert rec.action == "INSUFFICIENT_DATA"
    assert "valuation" in rec.missing_required_blocks
    assert "trend_cycle" in rec.missing_required_blocks

def test_research_factor_exclusion():
    """Ensure research-only factors are correctly categorized."""
    engine = AdvisoryEngine()
    
    # Valid strategic factors to get out of INSUFFICIENT_DATA
    obs = [
        create_obs("MVRV_Proxy", 8.0),
        create_obs("200WMA", 8.0),
        create_obs("Net_Liquidity", 8.0),
        create_obs("Options_Wall", 10.0), # Research factor
    ]
    
    rec = engine.evaluate(obs)
    
    # Decisional factors should be in supporting (since action is ADD)
    assert "MVRV_Proxy" in rec.supporting_factors
    # Research factor should be in excluded list
    assert "Options_Wall" in rec.excluded_research_factors
    assert "Options_Wall" not in rec.supporting_factors

def test_fail_closed_on_tactical_conflict():
    """Ensure engine fails closed (HOLD) if strategic is ADD but tactical is BEARISH."""
    engine = AdvisoryEngine()
    
    obs = [
        create_obs("MVRV_Proxy", 10.0), # Strategic Bullish
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0),
        create_obs("Short_Term_Stretch", -10.0), # Tactical Bearish
        create_obs("RSI_Weekly", -10.0)
    ]
    
    rec = engine.evaluate(obs)
    
    assert rec.strategic_regime == StrategicRegime.BULLISH_ACCUMULATION.value
    assert rec.tactical_state == "BEARISH_CONFIRMED"
    assert rec.action == "HOLD" # Blocked ADD
    assert "Strategic blocks are incomplete" not in rec.blocked_reasons # Not missing data
    assert "overstretched" in rec.summary.lower()
