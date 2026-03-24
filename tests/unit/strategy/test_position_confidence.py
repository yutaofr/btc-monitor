import pytest
from src.strategy.position_advisory_engine import PositionAdvisoryEngine
from src.strategy.factor_models import FactorObservation
from datetime import datetime

def make_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name,
        score=score,
        is_valid=is_valid,
        details={},
        description="",
        timestamp=datetime.now(),
        freshness_ok=True,
        confidence_penalty=0.0,
        blocked_reason=""
    )

def test_confidence_monotonicity_bullish():
    """Verify confidence increase with stronger bullish evidence."""
    engine = PositionAdvisoryEngine()
    
    # Base observations (incomplete but enough for bullish)
    obs_weak = [
        make_obs("MVRV_Proxy", 6.0),
        make_obs("Puell_Multiple", 6.0),
        make_obs("200WMA", 6.0),
    ]
    
    obs_strong = [
        make_obs("MVRV_Proxy", 8.0),
        make_obs("Puell_Multiple", 8.0),
        make_obs("200WMA", 8.0),
        make_obs("Cycle_Pos", 8.0),
        make_obs("Net_Liquidity", 8.0),
    ]
    
    rec_weak = engine.evaluate(obs_weak)
    rec_strong = engine.evaluate(obs_strong)
    
    assert rec_strong.confidence >= rec_weak.confidence

def test_confidence_determinism():
    """Verify same observations yield same confidence."""
    engine = PositionAdvisoryEngine()
    obs = [make_obs("MVRV_Proxy", 6.0), make_obs("200WMA", 6.0)]
    
    rec1 = engine.evaluate(obs)
    rec2 = engine.evaluate(obs)
    
    assert rec1.confidence == rec2.confidence

def test_low_quality_evidence_is_insufficient_data():
    """Verify all-invalid observations yield INSUFFICIENT_DATA (fail-closed)."""
    engine = PositionAdvisoryEngine()
    obs = [
        make_obs("MVRV_Proxy", 6.0, is_valid=False),
        make_obs("200WMA", 6.0, is_valid=False),
        make_obs("Net_Liquidity", 6.0, is_valid=False),
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "INSUFFICIENT_DATA"
