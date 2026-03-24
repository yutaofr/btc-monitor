import pytest
from datetime import datetime
from src.strategy.factor_models import FactorDefinition, FactorObservation, Recommendation

def test_factor_definition_initialization():
    definition = FactorDefinition(
        name="MVRV_Proxy",
        layer="strategic",
        block="valuation",
        source_class="on_chain",
        is_required_for_add=True,
        is_required_for_reduce=False,
        is_required_for_buy_now=True,
        is_wait_veto=False,
        is_backtestable=True,
        freshness_ttl_hours=24,
        default_weight=1.5,
        confidence_class="medium"
    )
    assert definition.name == "MVRV_Proxy"
    assert definition.layer == "strategic"
    assert definition.block == "valuation"

def test_factor_observation_initialization():
    obs = FactorObservation(
        name="MVRV_Proxy",
        score=8.0,
        is_valid=True,
        details={"raw_value": 1.2},
        description="Strong buy signal",
        timestamp=datetime.now(),
        freshness_ok=True,
        confidence_penalty=0.0,
        blocked_reason=""
    )
    assert obs.name == "MVRV_Proxy"
    assert obs.score == 8.0
    assert obs.is_valid is True

def test_recommendation_initialization():
    rec = Recommendation(
        action="ADD",
        confidence=85,
        strategic_regime="BULLISH_ACCUMULATION",
        tactical_state="FAVORABLE_ADD",
        supporting_factors=["MVRV_Proxy", "Puell_Multiple"],
        conflicting_factors=[],
        missing_required_blocks=[],
        missing_required_factors=[],
        blocked_reasons=[],
        freshness_warnings=[],
        excluded_research_factors=[],
        summary="Clear ADD signal."
    )
    assert rec.action == "ADD"
    assert rec.confidence == 85
    assert rec.strategic_regime == "BULLISH_ACCUMULATION"
