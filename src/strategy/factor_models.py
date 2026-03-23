from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class FactorDefinition:
    """Metadata contract for a factor."""
    name: str
    layer: str
    block: str
    source_class: str
    is_required_for_add: bool
    is_required_for_reduce: bool
    is_backtestable: bool
    freshness_ttl_hours: int
    default_weight: float
    confidence_class: str

@dataclass
class FactorObservation:
    """Runtime output of a factor calculation."""
    name: str
    score: float
    is_valid: bool
    details: Dict[str, Any]
    description: str
    timestamp: datetime
    freshness_ok: bool
    confidence_penalty: float
    blocked_reason: str

@dataclass
class Recommendation:
    """Top-level output object from the advisory engine."""
    action: str
    confidence: int
    strategic_regime: str
    tactical_state: str
    supporting_factors: List[str]
    conflicting_factors: List[str]
    missing_required_blocks: List[str]
    missing_required_factors: List[str]
    blocked_reasons: List[str]
    freshness_warnings: List[str]
    excluded_research_factors: List[str]
    summary: str
