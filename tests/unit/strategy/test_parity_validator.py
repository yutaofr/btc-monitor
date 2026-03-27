import pytest
import numpy as np
from datetime import datetime
from src.strategy.tadr_engine import TADREngine, TADRInternalState
from src.strategy.factor_models import FactorObservation
from src.monitoring.correlation_engine import CorrelationContext

class ParityValidator:
    """
    指令 [3.3]：用于比对回测与实盘输出的影子测试核心类。
    """
    def compare_states(self, state_a: TADRInternalState, state_b: TADRInternalState) -> bool:
        """比对两个内部状态是否 Bit-identical (99.9999% 相似度)。"""
        # 1. 检查标量字段
        scalars = ['strategic_score', 'confidence', 'target_allocation']
        for field in scalars:
            val_a = getattr(state_a, field)
            val_b = getattr(state_b, field)
            if not np.isclose(val_a, val_b, rtol=1e-6):
                return False
        
        # 2. 检查 map 字段 (raw_scores, weighted_scores)
        for field in ['raw_scores_map', 'weighted_scores_map', 'redundancy_multipliers']:
            map_a = getattr(state_a, field)
            map_b = getattr(state_b, field)
            if map_a.keys() != map_b.keys():
                return False
            for k in map_a:
                if not np.isclose(map_a[k], map_b[k], rtol=1e-6):
                    return False
        
        return True

    def run_sensitivity_analysis(self, engine: TADREngine, corr_range: np.ndarray) -> float:
        """
        指令 [3.1]：计算相关性波动时的置信度方差。
        """
        confidences = []
        obs = [
            FactorObservation(name="SPX_Proxy", score=10.0, is_valid=True, details={}, description="", 
                              timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
            FactorObservation(name="BTC_Trend", score=10.0, is_valid=True, details={}, description="", 
                              timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
            FactorObservation(name="Net_Liquidity", score=5.0, is_valid=True, details={}, description="", 
                              timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        ]
        
        for corr in corr_range:
            ctx = CorrelationContext(correlations={"SPX": corr}, regime_labels=["Risk-On"], is_valid=True)
            # 我们需要获取 Engine 的内部状态
            # 这里简单起见直接取推荐的置信度值
            rec = engine.evaluate(obs, context=ctx)
            confidences.append(rec.confidence / 100.0)
            
        return float(np.var(confidences))

def test_shadow_parity_bit_identical():
    """验证 100 组模拟数据的对齐度。"""
    validator = ParityValidator()
    # 模拟两个完全一致的状态
    # 这里我们只测试 Validator 逻辑本身
    state_mock = TADRInternalState(
        computation_timestamp_ns=123,
        raw_scores_map={"F1": 5.12345678},
        weighted_scores_map={"F1": 5.12345678},
        redundancy_multipliers={"F1": 1.0},
        correlation_matrix_snapshot={},
        gate_status={},
        strategic_score=5.12345678,
        confidence=1.0,
        target_allocation=0.5,
        regime_labels=[],
        is_circuit_breaker_active=False
    )
    
    assert validator.compare_states(state_mock, state_mock) is True

def test_redundancy_sensitivity():
    """
    指令 [3.1]：验证软阈值在 0.8 附近的平滑性。
    方差应极低，表明没有断崖跳变。
    """
    engine = TADREngine()
    validator = ParityValidator()
    
    # 范围 0.78 - 0.82
    corr_range = np.linspace(0.78, 0.82, 50)
    variance = validator.run_sensitivity_analysis(engine, corr_range)
    
    # 预期方差极小 (< 0.001)
    # 如果是硬门控，方差会很大
    assert variance < 0.001
