import pytest
from datetime import datetime
from src.strategy.strategic_engine import StrategicEngine, StrategicRegime
from src.strategy.factor_models import FactorObservation

def create_obs(name, score):
    return FactorObservation(
        name=name, score=score, is_valid=True, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_strategic_engine_outputs_allowed_regimes():
    engine = StrategicEngine()
    
    # Needs all 3 blocks for BULLISH
    obs = [
        create_obs("MVRV_Proxy", 10.0), 
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0)
    ]
    
    regime = engine.infer_regime(obs)
    assert isinstance(regime, StrategicRegime)
    assert regime == StrategicRegime.BULLISH_ACCUMULATION

def test_missing_blocks_returns_insufficient_data():
    engine = StrategicEngine()
    obs = [
        create_obs("MVRV_Proxy", 8.0),
        # Missing trend_cycle and macro
    ]
    regime = engine.infer_regime(obs)
    assert regime == StrategicRegime.INSUFFICIENT_DATA

def test_overheated_requires_two_blocks():
    engine = StrategicEngine()
    # Trend is -10 (Overheated), Macro is -5 (Overheated)
    obs = [
        create_obs("200WMA", -10.0), 
        create_obs("Net_Liquidity", -10.0),
        create_obs("MVRV_Proxy", 0.0) # Valuation valid but neutral
    ]
    regime = engine.infer_regime(obs)
    assert regime == StrategicRegime.OVERHEATED

def test_tactical_factors_ignored():
    engine = StrategicEngine()
    # Provide all required strategic factors at neutral scores
    obs = [
        create_obs("MVRV_Proxy", 0.0),
        create_obs("200WMA", 0.0),
        create_obs("Net_Liquidity", 0.0),
        # Strong tactical bullish signal
        create_obs("FearGreed", 10.0)
    ]
    regime = engine.infer_regime(obs)
    assert regime == StrategicRegime.NEUTRAL
