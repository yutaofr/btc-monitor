import pytest
from datetime import datetime
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation

def create_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name, score=score, is_valid=is_valid, details={}, description="",
        timestamp=datetime.now(), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_missing_required_factors_population():
    """Ensure missing_required_factors is populated when an ADD is blocked."""
    engine = AdvisoryEngine()
    
    # Bullish valuation and trend, but missing 'Yields' (required for ADD)
    obs = [
        create_obs("MVRV_Proxy", 8.0),
        create_obs("Puell_Multiple", 8.0),
        create_obs("200WMA", 8.0),
        create_obs("Cycle_Pos", 8.0),
        create_obs("Net_Liquidity", 8.0),
        # create_obs("Yields", 8.0),  <-- Deliberately missing
    ]
    
    rec = engine.evaluate(obs)
    
    assert rec.action == "HOLD"
    assert "Yields" in rec.missing_required_factors
    assert "Blocked ADD" in rec.summary

def test_research_factor_exclusion_from_confluence():
    """Ensure research-only factors do not leak into supporting/conflicting lists."""
    engine = AdvisoryEngine()
    
    obs = [
        create_obs("MVRV_Proxy", 8.0),
        create_obs("Puell_Multiple", 8.0),
        create_obs("200WMA", 8.0),
        create_obs("Cycle_Pos", 8.0),
        create_obs("Net_Liquidity", 8.0),
        create_obs("Yields", 8.0),
        create_obs("Options_Wall", 10.0), # Research factor
        create_obs("ETF_Flow", -10.0),    # Research factor
    ]
    
    rec = engine.evaluate(obs)
    
    # Research factors should be in excluded list, NOT in supporting/conflicting
    assert "Options_Wall" in rec.excluded_research_factors
    assert "ETF_Flow" in rec.excluded_research_factors
    assert "Options_Wall" not in rec.supporting_factors
    assert "ETF_Flow" not in rec.conflicting_factors
    
    # Decisional factors should still be there
    assert "MVRV_Proxy" in rec.supporting_factors
