from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

class Layer(str, Enum):
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    RESEARCH = "research"

class PositionAction(str, Enum):
    ADD = "ADD"
    REDUCE = "REDUCE"
    HOLD = "HOLD"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class CashAction(str, Enum):
    BUY_NOW = "BUY_NOW"
    STAGGER_BUY = "STAGGER_BUY"
    WAIT = "WAIT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class Action(str, Enum):
    # 通用枚举，兼容旧代码
    ADD = "ADD"
    REDUCE = "REDUCE"
    HOLD = "HOLD"
    BUY_NOW = "BUY_NOW"
    STAGGER_BUY = "STAGGER_BUY"
    WAIT = "WAIT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class FactorDefinition(BaseModel):
    """
    Metadata contract for a factor (Pydantic Version).
    Instruction [2.3]: Schema validation for weights and requirements.
    """
    name: str
    layer: Layer
    block: str
    source_class: str
    is_required_for_add: bool
    is_required_for_reduce: bool
    is_required_for_buy_now: bool
    is_wait_veto: bool
    is_backtestable: bool
    freshness_ttl_hours: int = Field(ge=0, le=720) # Max 1 month
    default_weight: float = Field(ge=0.0, le=10.0) # Constraint: Max weight 10.0
    confidence_class: str
    is_critical: bool = False # V3 Gating Feature

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Factor name cannot be empty')
        return v

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
