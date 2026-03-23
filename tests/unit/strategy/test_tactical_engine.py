import pytest
from datetime import datetime
from src.strategy.tactical_engine import TacticalEngine
from src.strategy.factor_models import FactorObservation

def create_obs(name, score):
    return FactorObservation(
        name=name, score=score, is_valid=True, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_tactical_engine_outputs_allowed_states():
    engine = TacticalEngine()
    obs = [create_obs("RSI_Div", 10.0), create_obs("FearGreed", 8.0)]
    state = engine.evaluate_tactical(obs)
    assert state in ["FAVORABLE_ADD", "NEUTRAL", "FAVORABLE_REDUCE", "INSUFFICIENT_DATA"]

    obs_neutral = [create_obs("RSI_Div", 0.0), create_obs("FearGreed", 0.0)]
    state_neutral = engine.evaluate_tactical(obs_neutral)
    assert state_neutral == "NEUTRAL"

def test_tactical_engine_favorable_states():
    engine = TacticalEngine()
    # Bullish
    assert engine.evaluate_tactical([create_obs("RSI_Div", 10.0), create_obs("FearGreed", 10.0)]) == "FAVORABLE_ADD"
    # Bearish
    assert engine.evaluate_tactical([create_obs("RSI_Div", -10.0), create_obs("FearGreed", -10.0)]) == "FAVORABLE_REDUCE"

def test_tactical_missing_data():
    engine = TacticalEngine()
    # Empty observations or missing required ones (RSI_Div & FearGreed)
    state = engine.evaluate_tactical([])
    assert state == "INSUFFICIENT_DATA"

def test_tactical_cannot_create_structural_add():
    engine = TacticalEngine()
    state = engine.evaluate_tactical([create_obs("RSI_Div", 10.0), create_obs("FearGreed", 10.0)])
    assert state != "ADD" # Must return tactical states only
