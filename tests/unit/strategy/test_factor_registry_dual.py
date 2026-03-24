import pytest
from src.strategy.factor_registry import get_factor
from src.strategy.factor_models import FactorDefinition

def test_factor_definition_dual_fields():
    """Verify FactorDefinition has the new required fields for dual-decision."""
    # This should fail if the attributes are missing
    try:
        f = get_factor("MVRV_Proxy")
        assert hasattr(f, "is_required_for_buy_now")
        assert hasattr(f, "is_wait_veto")
    except KeyError:
        pytest.fail("MVRV_Proxy should be in registry")

def test_registry_population():
    """Verify registry has at least some factors with dual-branch requirements set."""
    f = get_factor("MVRV_Proxy")
    # MVRV is usually required for buying
    assert f.is_required_for_buy_now is True
    
    # 200WMA is usually required for add and buy
    f2 = get_factor("200WMA")
    assert f2.is_required_for_add is True
    assert f2.is_required_for_buy_now is True
