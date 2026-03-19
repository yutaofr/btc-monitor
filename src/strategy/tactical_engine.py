from src.strategy.policies import TACTICAL_FACTORS, TACTICAL_WEIGHTS


class TacticalEngine:
    def _relevant_results(self, results):
        for result in results:
            if result.name in TACTICAL_FACTORS and result.is_valid:
                yield result

    def calculate_score(self, results):
        valid_weighted_sum = 0.0
        total_weight = 0.0

        for result in self._relevant_results(results):
            weight = TACTICAL_WEIGHTS.get(result.name, result.weight)
            valid_weighted_sum += result.score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round((valid_weighted_sum / total_weight) * 10, 2)
