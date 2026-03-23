import pytest
from datetime import datetime
from src.strategy.strategic_engine import StrategicEngine
from src.strategy.factor_models import FactorObservation

def create_obs(name, score, block):
    # Dummy block assignment for testing without relying on deep registry changes inside test
    return FactorObservation(
        name=name, score=score, is_valid=True, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_strategic_engine_outputs_allowed_regimes():
    engine = StrategicEngine()
    
    obs = [
        create_obs("MVRV_Proxy", 8.0, "valuation"),
        create_obs("200WMA", 6.0, "trend_cycle"),
        create_obs("Net_Liquidity", 5.0, "macro_liquidity")
    ]
    
    regime = engine.evaluate_regime(obs)
    assert regime in ["BULLISH_ACCUMULATION", "NEUTRAL", "OVERHEATED", "RISK_OFF", "INSUFFICIENT_DATA"]

def test_missing_blocks_returns_insufficient_data():
    engine = StrategicEngine()
    obs = [
        create_obs("MVRV_Proxy", 8.0, "valuation"),
        # Missing trend_cycle and macro
    ]
    regime = engine.evaluate_regime(obs)
    assert regime == "INSUFFICIENT_DATA"

def test_tactical_factors_ignored():
    engine = StrategicEngine()
    # Provide all required strategic factors with neutral scores
    obs = [
        create_obs("MVRV_Proxy", 0.0, "valuation"),
        create_obs("200WMA", 0.0, "trend_cycle"),
        create_obs("Net_Liquidity", 0.0, "macro_liquidity"),
        # Strong tactical bullish signal
        create_obs("RSI_Div", 10.0, "sentiment_tactical")
    ]
    regime = engine.evaluate_regime(obs)
    # The tactical signal should not make it bullish
    assert regime == "NEUTRAL"
