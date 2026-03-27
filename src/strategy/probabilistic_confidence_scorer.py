from typing import List, Dict, Optional, Tuple
import numpy as np
from src.strategy.factor_models import FactorObservation
from src.monitoring.correlation_engine import CorrelationContext

class ProbabilisticConfidenceScorer:
    """
    TADR Architecture: Confidence Layer
    Implements smooth redundancy decay, fail-closed logic, and provides 
    intermediate calculation metadata for shadow testing.
    """

    def calculate_with_metadata(self, observations: List[FactorObservation], 
                               weights: Dict[str, float], 
                               context: Optional[CorrelationContext] = None,
                               critical_factors: Optional[List[str]] = None) -> Tuple[float, Dict[str, float], Dict[str, bool]]:
        """
        Calculates a confidence score AND returns multipliers/gates.
        Returns: (confidence, redundancy_multipliers, gate_status)
        """
        if not observations:
            return 0.0, {}, {}

        # 1. 核心因子硬拦截 (Hard Gating / Fail-Closed)
        if critical_factors is None:
            critical_factors = ["Net_Liquidity", "MVRV_Proxy", "Puell_Multiple"]
        
        gate_status = {}
        invalid_critical_count = 0
        for name in critical_factors:
            obs = next((o for o in observations if o.name == name), None)
            is_valid = obs.is_valid if obs else False
            gate_status[name] = not is_valid
            if not is_valid:
                invalid_critical_count += 1
        
        # 指令 [2.2]：如果缺失 2 个以上核心因子，强制归零 (Fail-Closed)
        if invalid_critical_count >= 2:
            return 0.0, {}, gate_status

        # 2. 信息熵衰减 (Entropy Decay)
        eta = self._calculate_entropy_decay(observations, weights)

        # 3. 相关性去冗余惩罚 (Redundancy Penalty)
        multipliers = {o.name: 1.0 for o in observations if o.is_valid}
        total_redundancy_penalty = 1.0

        if context and context.is_valid:
            spx_corr = context.correlations.get("SPX", 0.0)
            related_factors = ["SPX_Proxy", "BTC_Trend"]
            active_related = [o for o in observations if o.name in related_factors and o.is_valid]
            
            if len(active_related) > 1:
                # [SMOOTH FORMULA]
                theta = 0.8
                k = 15
                max_p = 0.4
                z = k * (abs(spx_corr) - theta)
                # 权重平滑压缩系数
                m = 1.0 - (max_p / (1 + np.exp(-z)))
                total_redundancy_penalty = m
                for factor in related_factors:
                    if factor in multipliers:
                        multipliers[factor] = m

        # 4. 一致性校验 (Confluence Check)
        confluence = self._calculate_confluence_multiplier(observations, weights)

        final_confidence = float(np.clip(eta * confluence * total_redundancy_penalty, 0.0, 1.0))
        return final_confidence, multipliers, gate_status

    def calculate(self, *args, **kwargs) -> float:
        """Legacy compatibility."""
        score, _, _ = self.calculate_with_metadata(*args, **kwargs)
        return score

    def _calculate_entropy_decay(self, observations: List[FactorObservation], weights: Dict[str, float]) -> float:
        total_weight = sum(weights.values())
        if total_weight == 0: return 1.0
        invalid_weight = 0.0
        for name, weight in weights.items():
            obs = next((o for o in observations if o.name == name), None)
            if not obs or not obs.is_valid or not obs.freshness_ok:
                invalid_weight += weight
        return max(0.0, 1.0 - (invalid_weight / total_weight))

    def _calculate_confluence_multiplier(self, observations: List[FactorObservation], weights: Dict[str, float]) -> float:
        valid_obs = [o for o in observations if o.is_valid]
        if not valid_obs: return 1.0
        weighted_sum = 0.0
        abs_weighted_sum = 0.0
        for obs in valid_obs:
            w = weights.get(obs.name, 1.0)
            weighted_sum += obs.score * w
            abs_weighted_sum += abs(obs.score) * w
        if abs_weighted_sum == 0: return 1.0
        alignment = abs(weighted_sum) / abs_weighted_sum
        return 0.5 + 0.5 * alignment
