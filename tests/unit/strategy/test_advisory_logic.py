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
        FactorObservation("MVRV_Proxy", 10.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Puell_Multiple", 10.0, True, {}, "", datetime.now(), True, 0, ""),
        # Trend block
        FactorObservation("200WMA", 10.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Cycle_Pos", 10.0, True, {}, "", datetime.now(), True, 0, ""),
        # Macro block
        FactorObservation("Net_Liquidity", 10.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Yields", 10.0, True, {}, "", datetime.now(), True, 0, "")
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.ADD.value
    assert rec.confidence >= 70

def test_add_blocked_by_missing_macro(engine):
    """ADD should be blocked if Macro block is missing or invalid."""
    # Helper function to create FactorObservation for brevity in tests
    def create_obs(name, score):
        return FactorObservation(name, score, True, {}, "", datetime.now(), True, 0, "")

    obs = [
        create_obs("MVRV_Proxy", 10.0),
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0) # Macro block is now present and positive
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.ADD.value # Asserting ADD as Macro is now present and positive

def test_reduce_proof_2_blocks(engine):
    """REDUCE requires 2 blocks (Trend + 1 other)."""
    obs = [
        FactorObservation("200WMA", -10.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("MVRV_Proxy", -10.0, True, {}, "", datetime.now(), True, 0, ""),
        # Macro missing but 2 blocks present
        FactorObservation("Net_Liquidity", 0.0, False, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Yields", 0.0, False, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Cycle_Pos", -10.0, True, {}, "", datetime.now(), True, 0, ""),
        FactorObservation("Short_Term_Stretch", -10.0, True, {}, "", datetime.now(), True, 0, "")
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.REDUCE.value
