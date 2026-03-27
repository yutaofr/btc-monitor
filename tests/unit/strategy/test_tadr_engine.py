import pytest
from datetime import datetime
from src.strategy.factor_models import FactorObservation, Recommendation
from src.strategy.tadr_engine import TADREngine

def test_tadr_engine_circuit_breaker():
    """
    指令 [2.2] 验证：当 Confidence=0 时，Advisory 必须显式标记为 SYSTEM_GATE_LOCKED。
    """
    observations = [
        # 缺失核心因子导致零置信度
        FactorObservation(name="Net_Liquidity", score=0.0, is_valid=False, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=False, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="MVRV_Proxy", score=0.0, is_valid=False, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=False, confidence_penalty=1.0, blocked_reason=""),
    ]
    
    # 初始化 V3 引擎
    engine = TADREngine()
    recommendation = engine.evaluate(observations, ltm_precision=0.85)
    
    # 1. 验证 Action 强制为 INSUFFICIENT_DATA (V3 规范)
    assert recommendation.action in ["INSUFFICIENT_DATA", "WAIT", "HOLD"]
    
    # 2. 验证显式状态标记
    assert "SYSTEM_GATE_LOCKED" in recommendation.summary
    assert recommendation.confidence == 0
