import pytest
from datetime import datetime
from src.strategy.factor_models import Recommendation
from src.strategy.reporting import build_advisory_report

def test_build_advisory_report_bullish():
    rec = Recommendation(
        action="ADD",
        confidence=90,
        strategic_regime="BULLISH",
        tactical_state="CONFIRMED_UP",
        supporting_factors=["MVRV_Proxy", "200WMA"],
        conflicting_factors=[],
        missing_required_blocks=[],
        missing_required_factors=[],
        blocked_reasons=[],
        freshness_warnings=[],
        excluded_research_factors=[],
        summary="Strong bullish confluence."
    )
    
    report = build_advisory_report(rec, current_price=65000.0)
    
    assert "**Action:** `ADD`" in report
    assert "**Confidence:** `90`" in report
    assert "**Regime:** `BULLISH`" in report
    assert "**Tactical State:** `CONFIRMED_UP`" in report
    assert "MVRV_Proxy" in report
    assert "Strong bullish confluence" in report

def test_build_advisory_report_blocked():
    rec = Recommendation(
        action="HOLD",
        confidence=40,
        strategic_regime="NEUTRAL",
        tactical_state="INSUFFICIENT_DATA",
        supporting_factors=["200WMA"],
        conflicting_factors=[],
        missing_required_blocks=["valuation"],
        missing_required_factors=["MVRV_Proxy"],
        blocked_reasons=["Missing required valuation block."],
        freshness_warnings=[],
        excluded_research_factors=[],
        summary="Insufficient evidence to proceed."
    )
    
    report = build_advisory_report(rec, current_price=65000.0)
    
    assert "**Action:** `HOLD`" in report
    assert "Blocked Reasons:" in report
    assert "Missing required valuation block." in report
    assert "**Missing Blocks:** valuation" in report
