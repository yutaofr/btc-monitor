from typing import List, Dict
from enum import Enum
from src.strategy.factor_models import FactorObservation, Layer, Action
from src.strategy.factor_registry import get_factor

class StrategicRegime(Enum):
    BULLISH_ACCUMULATION = "BULLISH_ACCUMULATION"
    NEUTRAL = "NEUTRAL"
    OVERHEATED = "OVERHEATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class StrategicEngine:
    """
    Infers the slow, cyclical regime based on independent evidence blocks.
    Strictly follows the '3-block proof' for bullish regimes and '2-block' for bearish.
    """
    def __init__(self):
        self.required_blocks = ["valuation", "trend_cycle", "macro_liquidity"]

    def infer_regime(self, observations: List[FactorObservation]) -> StrategicRegime:
        # Group valid observations by block
        blocks = {}
        for obs in observations:
            try:
                defn = get_factor(obs.name)
                # Compare string layer with enum value
                if defn.layer != Layer.STRATEGIC.value or not obs.is_valid:
                    continue
                
                if defn.block not in blocks:
                    blocks[defn.block] = []
                blocks[defn.block].append(obs)
            except KeyError:
                continue

        # Calculate block scores
        block_scores = {b: sum(o.score for o in obs_list) / len(obs_list) for b, obs_list in blocks.items()}

        # 1. Check for BULLISH_ACCUMULATION (Requires 3 blocks)
        if all(b in blocks for b in self.required_blocks): # Bullish Accumulation: Requires 3-block agreement
            if all(block_scores.get(b, 0) > 3.0 for b in self.required_blocks):
                return StrategicRegime.BULLISH_ACCUMULATION
        
        # 2. Check for OVERHEATED (Requires 2 blocks, at least one is trend_cycle)
        valid_blocks = list(blocks.keys())
        if len(valid_blocks) >= 2:
            if block_scores.get("trend_cycle", 0) < -4.0 and any(
                block_scores.get(b, 0) < -4.0 for b in valid_blocks if b != "trend_cycle"
            ):
                return StrategicRegime.OVERHEATED

        # 3. Handle INSUFFICIENT_DATA vs NEUTRAL
        # If we have all 3 blocks but no edge case, it's NEUTRAL
        if all(b in blocks for b in self.required_blocks):
            return StrategicRegime.NEUTRAL
            
        # If we are missing required blocks and couldn't find a trend-supported signal
        return StrategicRegime.INSUFFICIENT_DATA
