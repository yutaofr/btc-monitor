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

        # Calculate weighted block scores
        block_scores = {}
        for b, obs_list in blocks.items():
            weighted_sum = sum(o.score * get_factor(o.name).default_weight for o in obs_list)
            weight_total = sum(get_factor(o.name).default_weight for o in obs_list)
            block_scores[b] = weighted_sum / weight_total if weight_total > 0 else 0.0

        score_val = block_scores.get("valuation", 0.0)
        score_trd = block_scores.get("trend_cycle", 0.0)
        score_mac = block_scores.get("macro_liquidity", 0.0)

        # 1. OVERHEATED (Extreme Valuation AND Trend)
        if score_val < -3.5 and score_trd < -3.5:
            return StrategicRegime.OVERHEATED
        if score_val < -3.0 and score_trd < -3.0 and score_mac < -3.0:
            return StrategicRegime.OVERHEATED
            
        # 2. BULLISH_ACCUMULATION (Extreme Value or Trend with confirmation)
        if score_val > 4.0 and score_trd > 4.0:
            return StrategicRegime.BULLISH_ACCUMULATION
        if score_val > 3.0 and score_trd > 3.0 and score_mac > 3.0:
            return StrategicRegime.BULLISH_ACCUMULATION

        # 3. Handle NEUTRAL vs INSUFFICIENT_DATA
        if all(b in blocks for b in self.required_blocks):
            return StrategicRegime.NEUTRAL

        return StrategicRegime.INSUFFICIENT_DATA
