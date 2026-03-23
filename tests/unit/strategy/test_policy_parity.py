import pytest
from src.strategy.policies import (
    STRATEGIC_FACTORS,
    TACTICAL_FACTORS,
    RESEARCH_FACTORS,
    STRATEGIC_WEIGHTS,
    TACTICAL_WEIGHTS
)
from src.strategy.factor_registry import get_all_factors, get_factor

def test_registry_parity_with_policies():
    """Ensure policies.py correctly mirrors the registry."""
    factors = get_all_factors()
    
    # Check strategic
    strategic_registry = [f.name for f in factors if f.layer == "strategic"]
    assert set(STRATEGIC_FACTORS) == set(strategic_registry)
    for f in factors:
        if f.layer == "strategic":
            assert STRATEGIC_WEIGHTS[f.name] == f.default_weight

    # Check tactical
    tactical_registry = [f.name for f in factors if f.layer == "tactical"]
    assert set(TACTICAL_FACTORS) == set(tactical_registry)
    for f in factors:
        if f.layer == "tactical":
            assert TACTICAL_WEIGHTS[f.name] == f.default_weight

    # Check research
    research_registry = [f.name for f in factors if f.layer == "research"]
    assert set(RESEARCH_FACTORS) == set(research_registry)
