from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
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
    gate_status: Dict[str, Any]                # [NEW] 详细门控元数据 (Fail-Closed)
    strategic_score: float                     # 综合标准化得分
    confidence: float                          # 最终置信度
    target_allocation: float                   # 目标仓位 %
    regime_labels: List[str]
    is_circuit_breaker_active: bool

from src.strategy.factor_utils import quantize_score
from src.strategy.factor_registry import FactorRegistry, _default_registry
from src.strategy.factor_models import Action

class TADREngine:
    """
    The Orchestrator for BTC Monitor V3.0 (TADR).
    Integrates Scorer, Resolver and implements Circuit Breaker logic.
    """

    def __init__(self, floor: float = None, cap: float = None, registry: Optional[FactorRegistry] = None):
        self.scorer = ProbabilisticConfidenceScorer()
        self.resolver = AllocationResolver(floor=floor, cap=cap)
        self.registry = registry or _default_registry
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
        
        # 1. 因子基础权重 (从 Registry 获取) [指令 2.3]
        base_weights = self.registry.get_weights_map()
        critical_factors = self.registry.get_critical_factors()
        
        # 1.1 动态权重漂移 (Dynamic Weighting) [Spec 3.2 对齐]
        # W_adj = W_base * (1 + lambda * |rho|)
        # 默认 lambda=0.5 (可配置)
        drift_lambda = 0.5
        weights = {}
        for name, w_base in base_weights.items():
            if context and context.is_valid and name in context.correlations:
                rho = abs(context.correlations[name])
                weights[name] = quantize_score(w_base * (1 + drift_lambda * rho))
            else:
                weights[name] = w_base
        
        # 2. 计算置信度及元数据 (注入动态权重及核心因子列表) [指令 2.2]
        confidence, multipliers, gates = self.scorer.calculate_with_metadata(
            observations, weights, context, critical_factors=critical_factors
        )
        
        # 3. 计分聚合 (Bit-Identical Parity 强化)
        # 指令 [4.1]: 逐项乘法后立即量化，消除累积浮点误差
        raw_scores = {o.name: quantize_score(o.score) for o in observations}
        valid_observations = [o for o in observations if o.is_valid]
        
        # 对每一项乘法进行原子级量化
        weighted_terms = {o.name: quantize_score(raw_scores[o.name] * weights.get(o.name, 1.0)) 
                         for o in valid_observations}
        
        weighted_sum = sum(weighted_terms.values())
        norm_score = quantize_score(weighted_sum / max(1, sum(weights.values())))

        # 4. 熔断判定 (Explicit Circuit Breaker)
        is_circuit_breaker_active = (confidence == 0.0)
        
        # 5. 目标仓位解析
        target_allocation = self.resolver.map_to_allocation(norm_score, confidence, ltm_precision)
        
        # 6. 生成内部状态记录 (Shadow Testing Alignment) [指令 3.3]
        self.last_internal_state = TADRInternalState(
            computation_timestamp_ns=timestamp_ns,
            raw_scores_map=raw_scores,
            weighted_scores_map=weighted_terms, # 已通过原子级量化的加权分
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

        # 7. 生成最终建议 [指令 4.2] 统一语义映射
        if is_circuit_breaker_active:
            action = Action.INSUFFICIENT_DATA
            summary = "!! [SYSTEM_GATE_LOCKED] CRITICAL DATA MISSING (Macro/Valuation). Action suppressed !!"
        elif norm_score < -3.5:
            action = Action.REDUCE
            summary = f"TADR V3: Market Overheated (Score {norm_score:.1f}). Target reduced to {target_allocation:.1%}."
        elif target_allocation > (self.resolver.floor + 0.1): # 显著高于底仓才建议 ADD
            action = Action.ADD
            summary = f"TADR V3: Target Allocation {target_allocation:.1%}. Confidence {confidence:.2f}."
        else:
            action = Action.HOLD
            summary = f"TADR V3: Holding at/near base allocation ({target_allocation:.1%})."

        # 8. 因子归类 (仅包含有效因子) [指令 5.1]
        supporting = [o.name for o in valid_observations if o.score > 3]
        conflicting = [o.name for o in valid_observations if o.score < -3]
        missing_factors = [name for name, status in gates.items() if status["is_active"]]

        return Recommendation(
            action=action.value,
            confidence=int(confidence * 100),
            strategic_regime=", ".join(internal_state.regime_labels),
            tactical_state="CONFIRMED" if confidence > 0.6 else "UNCONFIRMED",
            supporting_factors=supporting,
            conflicting_factors=conflicting,
            missing_required_blocks=[], # Blocks can be inferred from missing_factors if needed
            missing_required_factors=missing_factors,
            blocked_reasons=missing_factors if is_circuit_breaker_active else [],
            freshness_warnings=[f"{o.name} stale" for o in observations if not o.freshness_ok],
            excluded_research_factors=[o.name for o in observations if weights.get(o.name) == 0.0],
            summary=summary
        )
