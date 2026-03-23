import pytest
from datetime import datetime, timedelta, timezone
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

def test_timezone_mismatch():
    """Verify that mixing aware and naive datetimes doesn't raise TypeError."""
    from datetime import timezone
    from src.strategy.factor_utils import check_freshness
    
    now_aware = datetime.now(timezone.utc)
    ts_naive = datetime.now() - timedelta(hours=10)
    
    # This should internally normalize and return True without crashing
    assert check_freshness(ts_naive, 24, current_time=now_aware) is True
    
    ts_stale_naive = datetime.now() - timedelta(hours=50)
    assert check_freshness(ts_stale_naive, 24, current_time=now_aware) is False

def test_future_date_rejection():
    """Verify that observations from the future are rejected as not fresh."""
    from src.strategy.factor_utils import check_freshness
    
    now = datetime.now(timezone.utc)
    future_ts = now + timedelta(hours=1)
    
    # Delta will be negative, should return False
    assert check_freshness(future_ts, 24, current_time=now) is False

def test_timezone_conversion_math():
    """Verify that mathematical deltas work correctly after forced UTC conversion."""
    from datetime import timezone, timedelta
    from src.strategy.factor_utils import check_freshness
    
    # Create a 'now' in UTC
    now_utc = datetime(2026, 3, 23, 12, 0, 0, tzinfo=timezone.utc)
    
    # Create a 'stale' time 25 hours ago, but naive
    stale_naive = datetime(2026, 3, 22, 11, 0, 0) 
    
    # check_freshness should treat stale_naive as UTC if naive
    # 12:00 (Today) - 11:00 (Yesterday) = 25 hours -> Stale for 24h TTL
    assert check_freshness(stale_naive, 24, current_time=now_utc) is False
    
    # Create a 'fresh' time 23 hours ago, but naive
    fresh_naive = datetime(2026, 3, 22, 13, 0, 0)
    assert check_freshness(fresh_naive, 24, current_time=now_utc) is True


