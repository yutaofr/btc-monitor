import pytest
from datetime import datetime, timedelta
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation

def test_freshness_warning_in_report():
    """Verify that a stale observation triggers a warning in the Recommendation."""
    engine = AdvisoryEngine()
    
    # Create an observation where freshness_ok=False
    stale_obs = FactorObservation(
        name="MVRV_Proxy",
        score=5.0,
        is_valid=True,
        confidence_penalty=0.0,
        details={},
        description="Stale data test",
        timestamp=datetime.now() - timedelta(days=5),
        freshness_ok=False, # Manually flagged as stale
        blocked_reason=""
    )
    
    rec = engine.evaluate([stale_obs])
    
    # AdvisoryEngine line 30-31: 
    # if not getattr(obs, "freshness_ok", True):
    #     freshness_warnings.append(f"{obs.name} data is stale")
    
    assert any("MVRV_Proxy data is stale" in w for w in rec.freshness_warnings)

def test_freshness_utility_logic():
    """Test the shared freshness utility directly."""
    from src.strategy.factor_utils import check_freshness
    
    now = datetime.now()
    ts_fresh = now - timedelta(hours=10)
    ts_stale = now - timedelta(hours=50)
    
    assert check_freshness(ts_fresh, 24, current_time=now) is True
    assert check_freshness(ts_stale, 24, current_time=now) is False
