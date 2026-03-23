"""
Factor registry and metadata configurations.
Replaces policies.py as the single source of truth for factor metadata.
"""
from typing import List, Dict
from src.strategy.factor_models import FactorDefinition

# Extracted from older policies.py, mapping to new blocks based on standard interpretation.
_REGISTRY = {
    "MVRV_Proxy": FactorDefinition(
        name="MVRV_Proxy",
        layer="strategic",
        block="valuation",
        source_class="on_chain",
        is_required_for_add=True,
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=48,
        default_weight=1.5,
        confidence_class="low"
    ),
    "Puell_Multiple": FactorDefinition(
        name="Puell_Multiple",
        layer="strategic",
        block="valuation",
        source_class="on_chain",
        is_required_for_add=True,
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=48,
        default_weight=1.2,
        confidence_class="medium"
    ),
    "200WMA": FactorDefinition(
        name="200WMA",
        layer="strategic",
        block="trend_cycle",
        source_class="price",
        is_required_for_add=True,
        is_required_for_reduce=True,
        is_backtestable=True,
        freshness_ttl_hours=48,
        default_weight=1.0,
        confidence_class="high"
    ),
    "Cycle_Pos": FactorDefinition(
        name="Cycle_Pos",
        layer="strategic",
        block="trend_cycle",
        source_class="price",
        is_required_for_add=True,
        is_required_for_reduce=True,
        is_backtestable=True,
        freshness_ttl_hours=48,
        default_weight=1.0,
        confidence_class="medium"
    ),
    "Net_Liquidity": FactorDefinition(
        name="Net_Liquidity",
        layer="strategic",
        block="macro_liquidity",
        source_class="macro",
        is_required_for_add=True,
        is_required_for_reduce=True,
        is_backtestable=True,
        freshness_ttl_hours=168, # 1 week
        default_weight=1.0,
        confidence_class="medium"
    ),
    "DXY_Regime": FactorDefinition(
        name="DXY_Regime",
        layer="strategic",
        block="macro_liquidity",
        source_class="macro",
        is_required_for_add=False,  # Provides additional macro context
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=168,
        default_weight=1.0,
        confidence_class="medium"
    ),
    "Yields": FactorDefinition(
        name="Yields",
        layer="strategic",
        block="macro_liquidity",
        source_class="macro",
        is_required_for_add=True,
        is_required_for_reduce=True,
        is_backtestable=True,
        freshness_ttl_hours=168,
        default_weight=1.0,
        confidence_class="medium"
    ),
    "Hash_Ribbon": FactorDefinition(
        name="Hash_Ribbon",
        layer="strategic",
        block="valuation",
        source_class="on_chain",
        is_required_for_add=False,  # Not strictly required, but provides alternative evidence
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=48,
        default_weight=1.0,
        confidence_class="high"
    ),
    
    # Tactical Factors
    "RSI_Div": FactorDefinition(
        name="RSI_Div",
        layer="tactical",
        block="sentiment_tactical",
        source_class="price",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=24,
        default_weight=1.0,
        confidence_class="medium"
    ),
    "FearGreed": FactorDefinition(
        name="FearGreed",
        layer="tactical",
        block="sentiment_tactical",
        source_class="sentiment",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=24,
        default_weight=1.0,
        confidence_class="medium"
    ),
    "Short_Term_Stretch": FactorDefinition(
        name="Short_Term_Stretch",
        layer="tactical",
        block="sentiment_tactical",
        source_class="price",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=True,
        freshness_ttl_hours=24,
        default_weight=1.0,
        confidence_class="medium"
    ),
    
    # Research Factors
    "Production_Cost": FactorDefinition(
        name="Production_Cost",
        layer="research",
        block="valuation",
        source_class="on_chain",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=False,
        freshness_ttl_hours=48,
        default_weight=1.0,
        confidence_class="low"
    ),
    "Options_Wall": FactorDefinition(
        name="Options_Wall",
        layer="research",
        block="market_structure",
        source_class="derivatives",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=False,
        freshness_ttl_hours=24,
        default_weight=1.0,
        confidence_class="low"
    ),
    "ETF_Flow": FactorDefinition(
        name="ETF_Flow",
        layer="research",
        block="market_structure",
        source_class="derivatives",
        is_required_for_add=False,
        is_required_for_reduce=False,
        is_backtestable=False,
        freshness_ttl_hours=24,
        default_weight=1.0,
        confidence_class="low"
    ),
}

def get_all_factors() -> List[FactorDefinition]:
    """Return all registered factors."""
    return list(_REGISTRY.values())

def get_factor(name: str) -> FactorDefinition:
    """Return a registered factor by name, raising KeyError if missing."""
    if name not in _REGISTRY:
        raise KeyError(f"Factor '{name}' not found in registry.")
    return _REGISTRY[name]
