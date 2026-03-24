"""
Shared utilities for strategic block aggregation used by both advisory engines.
"""
from typing import Dict, List, Tuple
from src.strategy.factor_models import FactorObservation, Layer
from src.strategy.factor_registry import get_factor


def aggregate_strategic_blocks(
    observations: List[FactorObservation],
) -> Tuple[List[float], int]:
    """
    Group valid strategic observations by block and return per-block means and
    total strategic factor count.

    Returns:
        block_means: List of mean scores, one per block that has ≥1 valid observation.
        strategic_factor_count: Total number of valid strategic factor observations.
    """
    raw_blocks: Dict[str, List[float]] = {}
    for obs in observations:
        try:
            defn = get_factor(obs.name)
        except KeyError:
            continue
        if defn.layer == Layer.STRATEGIC.value and obs.is_valid:
            raw_blocks.setdefault(defn.block, []).append(obs.score)

    block_means = [sum(scores) / len(scores) for scores in raw_blocks.values() if scores]
    strategic_factor_count = sum(len(s) for s in raw_blocks.values())
    return block_means, strategic_factor_count


def compute_agreement_weight(block_means: List[float]) -> float:
    """Sum of absolute block means — measures overall strategic conviction."""
    return sum(abs(m) for m in block_means)
