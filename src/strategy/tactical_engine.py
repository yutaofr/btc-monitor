from typing import List, Dict
from src.strategy.factor_models import FactorObservation, Layer

class TacticalEngine:
    """
    Provides short-horizon confirmation or tactical setup status.
    Uses sentiment, tactical RSI, and short-term stretch.
    """
    def __init__(self):
        pass

    def evaluate_tactical(self, observations: List[FactorObservation]) -> Dict:
        """
        Returns a summary of tactical evidence.
        """
        tactical_obs = [o for o in observations if get_layer(o.name) == Layer.TACTICAL.value and o.is_valid]
        
        if not tactical_obs:
            return {"tactical_bias": "NEUTRAL", "tactical_score": 0.0, "counts": 0}

        avg_score = sum(o.score for o in tactical_obs) / len(tactical_obs)
        
        bias = "NEUTRAL"
        if avg_score > 5.0: bias = "BULLISH_CONFIRMED"
        elif avg_score < -5.0: bias = "BEARISH_CONFIRMED"

        return {
            "tactical_bias": bias,
            "tactical_score": avg_score,
            "counts": len(tactical_obs)
        }

def get_layer(name: str):
    from src.strategy.factor_registry import get_factor
    try:
        return get_factor(name).layer
    except KeyError:
        return Layer.RESEARCH
