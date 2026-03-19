from src.strategy.policies import STRATEGIC_FACTORS, STRATEGIC_WEIGHTS


class StrategicEngine:
    def _relevant_results(self, results):
        for result in results:
            if result.name in STRATEGIC_FACTORS and result.is_valid:
                yield result

    def calculate_score(self, results):
        valid_weighted_sum = 0.0
        total_weight = 0.0

        for result in self._relevant_results(results):
            weight = STRATEGIC_WEIGHTS.get(result.name, result.weight)
            valid_weighted_sum += result.score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round((valid_weighted_sum / total_weight) * 10, 2)
