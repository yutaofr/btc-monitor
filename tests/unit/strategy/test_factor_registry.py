import pytest
from src.strategy.factor_registry import get_all_factors, get_factor

def test_registry_completeness():
    factors = get_all_factors()
    assert len(factors) > 0
    names = [f.name for f in factors]
    assert "MVRV_Proxy" in names
    assert "Puell_Multiple" in names
    assert "200WMA" in names

def test_registry_uniqueness():
    factors = get_all_factors()
    names = [f.name for f in factors]
    assert len(names) == len(set(names))

def test_get_factor():
    f = get_factor("MVRV_Proxy")
    assert f is not None
    assert f.name == "MVRV_Proxy"
    assert f.layer == "strategic"
    assert f.block == "valuation"

def test_get_nonexistent_factor():
    with pytest.raises(KeyError):
        get_factor("NONEXISTENT_FACTOR")
