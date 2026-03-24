import pytest
from datetime import datetime
from src.strategy.factor_models import FactorObservation
from src.strategy.advisory_engine import AdvisoryEngine

def test_add_gate_requires_consensus():
    """
    FR-7: ADD gate requires consensus.
    Previously required 3 blocks, now allows 2-block extreme agreement (Trend + Valuation).
    If only 1 block is present, it must return INSUFFICIENT_DATA.
    """
    # 1. Only Valuation Block
    obs_isolated = [
        FactorObservation(
            name="MVRV_Proxy", score=8.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        )
    ]
    engine = AdvisoryEngine()
    rec = engine.evaluate(obs_isolated)
    
    assert rec.action == "INSUFFICIENT_DATA"

def test_add_gate_succeeds_with_all_blocks():
    """
    Verify ADD with all three required blocks.
    """
    obs = [
        FactorObservation(
            name="MVRV_Proxy", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="200WMA", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="Net_Liquidity", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="FearGreed", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        )
    ]
    engine = AdvisoryEngine()
    rec = engine.evaluate(obs)
    
    # With all 3 blocks bullish and tactical confirmation, it should be ADD
    assert rec.action == "ADD"
    assert "MVRV_Proxy" in rec.supporting_factors
    assert "200WMA" in rec.supporting_factors
    assert "Net_Liquidity" in rec.supporting_factors

def test_add_requires_tactical_confirmation_when_not_overloaded():
    """
    Strong strategic evidence alone should not create ADD unless tactical confirmation is also present.
    """
    obs = [
        FactorObservation(
            name="MVRV_Proxy", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="200WMA", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="Net_Liquidity", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="FearGreed", score=0.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        )
    ]
    engine = AdvisoryEngine()
    rec = engine.evaluate(obs)

    assert rec.action == "HOLD"
    assert "Tactical confirmation required for ADD" in rec.summary

def test_add_requires_macro_confirmation_even_with_extreme_trend_and_value():
    """
    Two-block extremes should not produce ADD when macro confirmation is missing.
    """
    obs = [
        FactorObservation(
            name="MVRV_Proxy", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="200WMA", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="Net_Liquidity", score=0.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        ),
        FactorObservation(
            name="FearGreed", score=10.0, is_valid=True, details={}, description="",
            timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0, blocked_reason=""
        )
    ]
    engine = AdvisoryEngine()
    rec = engine.evaluate(obs)

    assert rec.action == "HOLD"
    assert rec.strategic_regime == "NEUTRAL"
