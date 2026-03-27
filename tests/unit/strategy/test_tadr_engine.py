import pytest
from datetime import datetime, timezone
from src.strategy.tadr_engine import TADREngine, TADRInternalState
from src.strategy.factor_models import FactorObservation, Action
from src.monitoring.correlation_engine import CorrelationContext
from src.strategy.factor_utils import quantize_score

@pytest.fixture
def tadr_engine():
    return TADREngine()

def create_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name, score=score, is_valid=is_valid, details={}, description="",
        timestamp=datetime.now(timezone.utc), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_tadr_dynamic_weighting(tadr_engine):
    """Verify weights are adjusted by correlation as per Spec 3.2."""
    obs = [create_obs("MVRV_Proxy", 10.0)]
    
    # 1. Base weights from registry
    base_weight = tadr_engine.registry.get_weights_map()["MVRV_Proxy"]
    
    # 2. Context with correlation
    # rho = 0.8, lambda = 0.5 => W_adj = W_base * (1 + 0.5 * 0.8) = W_base * 1.4
    context = CorrelationContext(
        is_valid=True,
        correlations={"MVRV_Proxy": 0.8},
        regime_labels=["Expansion"]
    )
    
    tadr_engine.evaluate(obs, context=context)
    internal_state = tadr_engine.last_internal_state
    
    expected_weight = quantize_score(base_weight * 1.4)
    raw_score = internal_state.raw_scores_map["MVRV_Proxy"]
    weighted_score = internal_state.weighted_scores_map["MVRV_Proxy"]
    
    assert weighted_score == quantize_score(raw_score * expected_weight)

def test_tadr_numerical_parity_quantization(tadr_engine):
    """Verify per-term quantization to ensure bit-identical parity."""
    score = 7.123456789
    obs = [create_obs("MVRV_Proxy", score)]
    
    tadr_engine.evaluate(obs)
    internal_state = tadr_engine.last_internal_state
    
    assert internal_state.raw_scores_map["MVRV_Proxy"] == quantize_score(score)
    
    weight = tadr_engine.registry.get_weights_map()["MVRV_Proxy"]
    expected_weighted = quantize_score(quantize_score(score) * weight)
    assert internal_state.weighted_scores_map["MVRV_Proxy"] == expected_weighted

def test_tadr_fail_closed_circuit_breaker(tadr_engine, mocker):
    """Verify circuit breaker logic (Fail-Closed)."""
    mocker.patch.object(tadr_engine.scorer, 'calculate_with_metadata', return_value=(0.0, {}, {"MVRV_Proxy": {"is_active": True}}))
    
    obs = [create_obs("MVRV_Proxy", 10.0)]
    rec = tadr_engine.evaluate(obs)
    
    assert rec.action == Action.INSUFFICIENT_DATA.value
    assert "SYSTEM_GATE_LOCKED" in rec.summary
    assert tadr_engine.last_internal_state.is_circuit_breaker_active is True

def test_tadr_action_mapping_add(tadr_engine, mocker):
    """Verify ADD action mapping in TADR."""
    mocker.patch.object(tadr_engine.scorer, 'calculate_with_metadata', return_value=(0.9, {}, {}))
    # Return a high allocation to trigger ADD
    mocker.patch.object(tadr_engine.resolver, 'map_to_allocation', return_value=0.8)
    
    obs = [create_obs("MVRV_Proxy", 8.0)]
    rec = tadr_engine.evaluate(obs)
    
    assert rec.action == Action.ADD.value
    assert "Target Allocation 80.0%" in rec.summary

def test_tadr_action_mapping_reduce(tadr_engine, mocker):
    """Verify REDUCE action mapping in TADR."""
    mocker.patch.object(tadr_engine.scorer, 'calculate_with_metadata', return_value=(0.9, {}, {}))
    mocker.patch.object(tadr_engine.resolver, 'map_to_allocation', return_value=0.2)
    
    # Need norm_score < -3.5. 
    # Mocking norm_score directly via obs is hard because of the normalization by total weight.
    # We will provide many negative factors.
    obs = [create_obs(name, -10.0) for name in tadr_engine.registry.get_weights_map().keys()]
    
    rec = tadr_engine.evaluate(obs)
    
    assert rec.action == Action.REDUCE.value
    assert "Market Overheated" in rec.summary
