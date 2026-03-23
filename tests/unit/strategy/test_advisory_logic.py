import pytest
from datetime import datetime
from src.strategy.advisory_engine import AdvisoryEngine
from src.strategy.factor_models import FactorObservation, Action

@pytest.fixture
def engine():
    return AdvisoryEngine()

def test_add_proof_3_blocks(engine):
    """ADD requires 3 strategic blocks (Valuation, Trend, Macro)."""
    obs = [
        # Valuation block
        FactorObservation("MVRV_Proxy", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Puell_Multiple", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        # Trend block
        FactorObservation("200WMA", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Cycle_Pos", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        # Macro block
        FactorObservation("Net_Liquidity", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Yields", 8.0, True, {}, "", datetime.now(), True, 0, "")
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.ADD.value
    assert rec.confidence >= 70

def test_add_blocked_by_missing_macro(engine):
    """ADD should be blocked if Macro block is missing or invalid."""
    obs = [
        FactorObservation("MVRV_Proxy", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("200WMA", 8.0, True, {}, "", datetime.now(), True, 0, ""),
        # Macro is missing
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.HOLD.value or rec.action == Action.INSUFFICIENT_DATA.value

def test_reduce_proof_2_blocks(engine):
    """REDUCE requires 2 blocks (Trend + 1 other)."""
    obs = [
        FactorObservation("200WMA", -8.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("MVRV_Proxy", -8.0, True, {}, "", datetime.now(), True, 0, ""),
        # Macro missing but 2 blocks present
        FactorObservation("Net_Liquidity", 0.0, False, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Yields", 0.0, False, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Cycle_Pos", -8.0, True, {}, "", datetime.now(), True, 0, "")
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.REDUCE.value
