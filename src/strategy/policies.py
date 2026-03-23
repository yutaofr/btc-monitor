"""Central policy definitions for strategy layers, now derived from the factor registry."""
from src.strategy.factor_registry import get_all_factors

_all_factors = get_all_factors()

STRATEGIC_FACTORS = tuple(f.name for f in _all_factors if f.layer == "strategic")
TACTICAL_FACTORS = tuple(f.name for f in _all_factors if f.layer == "tactical")
RESEARCH_FACTORS = tuple(f.name for f in _all_factors if f.layer == "research")

REQUIRED_STRATEGIC_FACTORS = tuple(f.name for f in _all_factors if f.layer == "strategic" and (f.is_required_for_add or f.is_required_for_reduce))

MIN_STRATEGIC_VALID_RATIO = 0.7

STRATEGIC_WEIGHTS = {f.name: f.default_weight for f in _all_factors if f.layer == "strategic"}
TACTICAL_WEIGHTS = {f.name: f.default_weight for f in _all_factors if f.layer == "tactical"}

RESEARCH_WEIGHT = 1.0

COMBINED_LAYER_WEIGHTS = {
    "strategic": 0.7,
    "tactical": 0.3,
}

def classify_factor(name, *, research_only=False):
    if research_only or name in RESEARCH_FACTORS:
        return "research"
    if name in STRATEGIC_FACTORS:
        return "strategic"
    if name in TACTICAL_FACTORS:
        return "tactical"
    return "unknown"

def is_research_factor(name, *, research_only=False):
    return classify_factor(name, research_only=research_only) == "research"
