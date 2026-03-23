import pytest
from datetime import datetime
from src.strategy.tactical_engine import TacticalEngine
from src.strategy.factor_models import FactorObservation

def create_obs(name, score):
    return FactorObservation(
        name=name, score=score, is_valid=True, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_tactical_engine_outputs_bias():
    engine = TacticalEngine()
    obs = [
        create_obs("FearGreed", 8.0),
        create_obs("RSI_Weekly", 6.0) # In registry, feargreed is tactical
    ]
    result = engine.evaluate_tactical(obs)
    assert "tactical_bias" in result
    assert result["tactical_bias"] == "BULLISH_CONFIRMED"

def test_tactical_missing_data():
    engine = TacticalEngine()
    obs = [
        # Only strategic factors
        create_obs("MVRV_Proxy", 8.0)
    ]
    result = engine.evaluate_tactical(obs)
    assert result["tactical_bias"] == "NEUTRAL"
    assert result["counts"] == 0
