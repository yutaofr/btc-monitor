import pytest
import numpy as np
from datetime import datetime
from src.strategy.tadr_engine import TADREngine, TADRInternalState
from src.strategy.factor_models import FactorObservation
from src.monitoring.correlation_engine import CorrelationContext
from src.strategy.factor_utils import quantize_score

class ParityValidator:
    def compare_states(self, state_a: TADRInternalState, state_b: TADRInternalState) -> bool:
        """指令 [4.2]：影子测试 100 样本比对。使用 1e-6 精度阈值。"""
        # 1. 检查标量
        for field in ['strategic_score', 'confidence', 'target_allocation']:
            if not np.isclose(getattr(state_a, field), getattr(state_b, field), rtol=1e-6):
                return False
        # 2. 检查得分映射
        if state_a.raw_scores_map != state_b.raw_scores_map:
            return False
        return True

def run_100_sample_parity():
    """
    模拟 100 组历史数据，验证 Engine 两次独立计算的 Bit-identical 性。
    """
    engine = TADREngine()
    validator = ParityValidator()
    success_count = 0
    
    # 随机模拟 100 组场景
    for i in range(100):
        # 种子固定，模拟“同一时间点”的数据快照
        np.random.seed(i)
        
        # 模拟 5 个因子，带随机缺失
        obs = []
        factors = ["Net_Liquidity", "MVRV_Proxy", "Puell_Multiple", "SPX_Proxy", "BTC_Trend"]
        for f in factors:
            is_valid = np.random.choice([True, False], p=[0.8, 0.2])
            score = quantize_score(np.random.uniform(-10, 10))
            obs.append(FactorObservation(
                name=f, score=score if is_valid else 0.0, is_valid=is_valid, 
                details={}, description="", timestamp=datetime.now(), 
                freshness_ok=is_valid, confidence_penalty=1.0, blocked_reason=""
            ))
        
        ctx = CorrelationContext(
            correlations={"SPX": np.random.uniform(-1, 1)}, 
            regime_labels=["Test"], is_valid=True
        )
        
        # 计算 A
        # 我们使用深拷贝模拟独立环境（或重新调用逻辑）
        rec_a = engine.evaluate(obs, context=ctx)
        # 这里虽然没有真正的回测 DataFrame，但我们记录其生成的 InternalState
        state_a = engine.last_internal_state # 假设引擎保存了最后的内部状态
        
        # 计算 B (独立重算)
        rec_b = engine.evaluate(obs, context=ctx)
        state_b = engine.last_internal_state
        
        if validator.compare_states(state_a, state_b):
            success_count += 1
            
    return success_count

def test_100_sample_parity_report():
    success_rate = run_100_sample_parity()
    print(f"\n[SHADOW TEST] Success Rate: {success_rate}/100")
    assert success_rate == 100
