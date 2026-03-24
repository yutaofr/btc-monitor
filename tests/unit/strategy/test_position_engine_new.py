import pytest
from src.strategy.position_advisory_engine import PositionAdvisoryEngine
from src.strategy.factor_models import PositionAction, FactorObservation
from datetime import datetime

def test_position_engine_exists():
    """Verify PositionAdvisoryEngine can be instantiated."""
    engine = PositionAdvisoryEngine()
    assert engine is not None

def test_position_engine_emits_position_actions():
    """Verify PositionAdvisoryEngine emissions are within PositionAction vocabulary."""
    engine = PositionAdvisoryEngine()
    # Mock some observations that would trigger a HOLD or INSUFFICIENT_DATA
    obs = [
        FactorObservation(
            name="MVRV_Proxy",
            score=0.0,
            is_valid=False,
            details={},
            description="",
            timestamp=datetime.now(),
            freshness_ok=True,
            confidence_penalty=0.0,
            blocked_reason=""
        )
    ]
    rec = engine.evaluate(obs)
    assert rec.action in [a.value for a in PositionAction]
