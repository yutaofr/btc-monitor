from typing import List
from src.strategy.factor_models import FactorObservation
from src.strategy.factor_registry import get_factor
from src.strategy.policies import TACTICAL_FACTORS, TACTICAL_WEIGHTS

class TacticalEngine:
    def evaluate_tactical(self, observations: List[FactorObservation]) -> str:
        """
        Evaluate tactical components to refine timing.
        Returns: FAVORABLE_ADD, NEUTRAL, FAVORABLE_REDUCE, or INSUFFICIENT_DATA.
        """
        tactical_scores = []
        
        for obs in observations:
            if not obs.is_valid:
                continue
                
            try:
                definition = get_factor(obs.name)
            except KeyError:
                continue
                
            if definition.layer == "tactical":
                tactical_scores.append(obs.score)
                
        if not tactical_scores:
            return "INSUFFICIENT_DATA"
            
        avg_score = sum(tactical_scores) / len(tactical_scores)
        
        if avg_score >= 5.0:
            return "FAVORABLE_ADD"
        elif avg_score <= -5.0:
            return "FAVORABLE_REDUCE"
        else:
            return "NEUTRAL"

    # Legacy methods for backward compatibility during migration
    def _relevant_results(self, results):
        for result in results:
            if result.name in TACTICAL_FACTORS and result.is_valid:
                yield result

    def calculate_score(self, results):
        valid_weighted_sum = 0.0
        total_weight = 0.0

        for result in self._relevant_results(results):
            weight = TACTICAL_WEIGHTS.get(result.name, getattr(result, 'weight', 1.0))
            valid_weighted_sum += getattr(result, 'score', 0.0) * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round((valid_weighted_sum / total_weight) * 10, 2)

