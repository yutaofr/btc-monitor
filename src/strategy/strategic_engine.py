from typing import List
from src.strategy.factor_models import FactorObservation
from src.strategy.factor_registry import get_factor
from src.strategy.policies import STRATEGIC_FACTORS, STRATEGIC_WEIGHTS

class StrategicEngine:
    def evaluate_regime(self, observations: List[FactorObservation]) -> str:
        """
        Evaluate strategic regime from slow factors only.
        Returns: BULLISH_ACCUMULATION, NEUTRAL, OVERHEATED, RISK_OFF, or INSUFFICIENT_DATA.
        """
        # Group observations by block
        blocks_present = set()
        block_scores = {"valuation": [], "trend_cycle": [], "macro_liquidity": []}

        for obs in observations:
            if not obs.is_valid:
                continue
            
            try:
                definition = get_factor(obs.name)
            except KeyError:
                continue

            # Only consider strategic blocks
            if definition.block in block_scores:
                blocks_present.add(definition.block)
                block_scores[definition.block].append(obs.score)

        # Check for missing required blocks
        if not {"valuation", "trend_cycle", "macro_liquidity"}.issubset(blocks_present):
            return "INSUFFICIENT_DATA"

        # Calculate average score for each block
        avg_scores = {
            block: sum(scores) / len(scores)
            for block, scores in block_scores.items()
            if scores
        }

        # Calculate overall strategic score
        overall_score = sum(avg_scores.values()) / len(avg_scores)

        # Map to regime rules (simplified)
        if overall_score >= 3.0:
            return "BULLISH_ACCUMULATION"
        elif overall_score <= -5.0:
            return "RISK_OFF"
        elif overall_score <= -2.0:
            return "OVERHEATED"
        else:
            return "NEUTRAL"

    # Legacy methods for backward compatibility during migration
    def _relevant_results(self, results):
        for result in results:
            if result.name in STRATEGIC_FACTORS and result.is_valid:
                yield result

    def calculate_score(self, results):
        valid_weighted_sum = 0.0
        total_weight = 0.0

        for result in self._relevant_results(results):
            weight = STRATEGIC_WEIGHTS.get(result.name, getattr(result, 'weight', 1.0))
            valid_weighted_sum += getattr(result, 'score', 0.0) * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round((valid_weighted_sum / total_weight) * 10, 2)


