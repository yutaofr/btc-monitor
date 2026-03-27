from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from src.strategy.factor_models import FactorObservation, Recommendation
from src.strategy.probabilistic_confidence_scorer import ProbabilisticConfidenceScorer
from src.strategy.allocation_resolver import AllocationResolver
from src.monitoring.correlation_engine import CorrelationContext

@dataclass
class TADRInternalState:
    """
    指令 [3.3]：影子测试核心数据结构，确保 Bit-identical 对齐。
    """
    computation_timestamp_ns: int               # 纳秒级时间戳
    raw_scores_map: Dict[str, float]           # 各因子原始分 (8位精度)
    weighted_scores_map: Dict[str, float]      # 加权后分值
    redundancy_multipliers: Dict[str, float]   # [NEW] Sigmoid 权重修正系数
    correlation_matrix_snapshot: Dict[str, float] # 相关性子阵
    gate_status: Dict[str, bool]               # [NEW] 硬门控触发掩码 (Fail-Closed)
    strategic_score: float                     # 综合标准化得分
    confidence: float                          # 最终置信度
    target_allocation: float                   # 目标仓位 %
    regime_labels: List[str]
    is_circuit_breaker_active: bool

from src.strategy.factor_utils import quantize_score

class TADREngine:
    """
    The Orchestrator for BTC Monitor V3.0 (TADR).
    Integrates Scorer, Resolver and implements Circuit Breaker logic.
    """

    def __init__(self, floor: float = 0.2, cap: float = 0.8):
        self.scorer = ProbabilisticConfidenceScorer()
        self.resolver = AllocationResolver(floor=floor, cap=cap)
        self.last_internal_state: Optional[TADRInternalState] = None

    def evaluate(self, observations: List[FactorObservation], 
                 ltm_precision: float = 0.85,
                 context: Optional[CorrelationContext] = None) -> Recommendation:
        """
        Main execution flow: Scorer -> Resolver -> Action Mapping
        """
        import time
        # 记录纳秒时间戳 [指令 3.3.5]
        timestamp_ns = time.time_ns()
        
        # 1. 因子权重 (暂用默认)
        weights = {obs.name: 1.0 for obs in observations}
        
        # 2. 计算置信度及元数据 [指令 3.3.3, 3.3.4]
        confidence, multipliers, gates = self.scorer.calculate_with_metadata(observations, weights, context)
        
        # 3. 计分聚合
        # 使用统一封装的 quantize_score [指令 4.1]
        raw_scores = {o.name: quantize_score(o.score) for o in observations}
        weighted_sum = sum(raw_scores[o.name] * weights.get(o.name, 1.0) for o in observations if o.is_valid)
        norm_score = quantize_score(weighted_sum / max(1, sum(weights.values())))

        # 4. 熔断判定 (Explicit Circuit Breaker)
        is_circuit_breaker_active = (confidence == 0.0)
        
        # 5. 目标仓位解析
        target_allocation = self.resolver.map_to_allocation(norm_score, confidence, ltm_precision)
        
        # 6. 生成内部状态记录 (Shadow Testing Alignment) [指令 3.3]
        self.last_internal_state = TADRInternalState(
            computation_timestamp_ns=timestamp_ns,
            raw_scores_map=raw_scores,
            weighted_scores_map={name: quantize_score(score * weights.get(name, 1.0)) for name, score in raw_scores.items()},
            redundancy_multipliers={name: quantize_score(m) for name, m in multipliers.items()},
            correlation_matrix_snapshot=context.correlations if context else {},
            gate_status=gates,
            strategic_score=norm_score,
            confidence=confidence,
            target_allocation=target_allocation,
            regime_labels=context.regime_labels if context else ["Unknown"],
            is_circuit_breaker_active=is_circuit_breaker_active
        )
        internal_state = self.last_internal_state

        # 7. 生成最终建议
        action = "HOLD" if target_allocation <= 0.2 else "ADD"
        if is_circuit_breaker_active:
            action = "WAIT" # 现金熔断
            summary = "!! [SYSTEM_GATE_LOCKED] CRITICAL DATA MISSING (Macro/Valuation). Action suppressed !!"
        else:
            summary = f"TADR V3: Target Allocation {target_allocation:.1%}. Confidence {confidence:.2f}."

        return Recommendation(
            action=action,
            confidence=int(confidence * 100),
            strategic_regime=", ".join(internal_state.regime_labels),
            tactical_state="Adaptive",
            supporting_factors=[o.name for o in observations if o.score > 0 and o.is_valid],
            conflicting_factors=[o.name for o in observations if o.score < 0 and o.is_valid],
            missing_required_blocks=[],
            missing_required_factors=[o.name for o in observations if not o.is_valid],
            blocked_reasons=["Circuit Breaker Active"] if is_circuit_breaker_active else [],
            freshness_warnings=[],
            excluded_research_factors=[],
            summary=summary
        )
