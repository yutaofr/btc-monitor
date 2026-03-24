import pytest
from datetime import datetime
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation, Action

def create_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name, score=score, is_valid=is_valid, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_confidence_monotonicity():
    """Traceability requirement: Ensure confidence reacts monotonically to alignment/conflict."""
    engine = AdvisoryEngine()
    
    # Base Bullish
    obs_base = [
        create_obs("MVRV_Proxy", 10.0), 
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0),
        create_obs("FearGreed", 0.0), # Tactical Neutral
    ]
    conf_neutral = engine.evaluate(obs_base).confidence
    
    # Aligned Bullish (Positive score for FearGreed means low Fear, which is bullish setup)
    # Actually FearGreed score is (50-val)/5. Low Val (Fear) = Positive Score.
    obs_aligned = obs_base[:-1] + [create_obs("FearGreed", 10.0)]
    conf_aligned = engine.evaluate(obs_aligned).confidence
    
    # Conflict Bearish tactical
    obs_conflict = obs_base[:-1] + [create_obs("FearGreed", -10.0)]
    conf_conflict = engine.evaluate(obs_conflict).confidence
    
    assert conf_aligned > conf_neutral > conf_conflict
