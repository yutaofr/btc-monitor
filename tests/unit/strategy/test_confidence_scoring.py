import pytest
from datetime import datetime
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation

def create_obs(name, score, confidence_penalty=0.0):
    return FactorObservation(
        name=name, score=score, is_valid=True, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=confidence_penalty, blocked_reason=""
    )

def test_confidence_monotonicity():
    """Ensure that better coverage and higher quality evidence increases confidence."""
    engine = AdvisoryEngine()
    
    # 1. Base weak ADD scenario
    obs_weak = [
        create_obs("MVRV_Proxy", 5.0),
        create_obs("Puell_Multiple", 1.0, confidence_penalty=10.0),
        create_obs("200WMA", 5.0),
        create_obs("Net_Liquidity", 1.0)
    ]
    rec_weak = engine.evaluate(obs_weak)
    
    # 2. Strong ADD scenario
    obs_strong = [
        create_obs("MVRV_Proxy", 8.0),
        create_obs("Puell_Multiple", 8.0),
        create_obs("200WMA", 8.0),
        create_obs("Cycle_Pos", 8.0),
        create_obs("Net_Liquidity", 8.0),
        create_obs("Yields", 8.0),
        create_obs("RSI_Div", 8.0),
        create_obs("FearGreed", 8.0)
    ]
    rec_strong = engine.evaluate(obs_strong)
    
    assert rec_strong.confidence > rec_weak.confidence

def test_low_confidence_downgrade():
    """Ensure recommendations below 60 are downgraded to HOLD."""
    engine = AdvisoryEngine()
    
    # Simulate a scenario that satisfies ADD structure but is extremely weak in confidence
    obs = [
        create_obs("MVRV_Proxy", 4.0, confidence_penalty=30.0),
        create_obs("Puell_Multiple", 4.0, confidence_penalty=30.0),
        create_obs("200WMA", 4.0, confidence_penalty=30.0),
        create_obs("Cycle_Pos", 4.0, confidence_penalty=30.0),
        create_obs("Net_Liquidity", 4.0, confidence_penalty=30.0),
        create_obs("Yields", 4.0, confidence_penalty=30.0)
    ]
    rec = engine.evaluate(obs)
    
    # It would be an ADD structurally, but downgraded to HOLD because confidence < 60
    assert rec.action == "HOLD"
    assert rec.confidence < 60
    assert "downgrad" in rec.summary.lower() or "mixed" in rec.summary.lower()

def test_insufficient_data_confidence():
    """INSUFFICIENT_DATA retains its action regardless of confidence."""
    engine = AdvisoryEngine()
    obs = [create_obs("MVRV_Proxy", 10.0)]
    rec = engine.evaluate(obs)
    assert rec.action == "INSUFFICIENT_DATA"
