import pytest
from datetime import datetime
from src.strategy.factor_models import FactorObservation
from src.strategy.probabilistic_confidence_scorer import ProbabilisticConfidenceScorer

def test_confidence_decay_on_missing_factors():
    """
    测试信息熵衰减：
    - 当一个权重为 1.0 的因子缺失（总权重 5.0）时，置信度应下降。
    - 预期衰减因子 eta = 1 - (1.0 / 5.0) = 0.8
    """
    observations = [
        FactorObservation(name="F1", score=5.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="F2", score=5.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="F3", score=5.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="F4", score=5.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        # 缺失 F5
        FactorObservation(name="F5", score=0.0, is_valid=False, details={}, description="", timestamp=datetime.now(), freshness_ok=False, confidence_penalty=1.0, blocked_reason="Missing"),
    ]
    
    # 模拟权重映射
    weights = {"F1": 1.0, "F2": 1.0, "F3": 1.0, "F4": 1.0, "F5": 1.0}
    
    scorer = ProbabilisticConfidenceScorer()
    confidence = scorer.calculate(observations, weights, context=None, critical_factors=[])
    
    # 验证置信度接近 0.8 (因为 F5 缺失，占总权重的 20%)
    assert confidence == pytest.approx(0.8, abs=0.01)

def test_confidence_confluence_bonus():
    """测试一致性奖励：当所有因子方向一致时，置信度维持在最高。"""
    observations = [
        FactorObservation(name="F1", score=8.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="F2", score=7.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
    ]
    weights = {"F1": 1.0, "F2": 1.0}
    scorer = ProbabilisticConfidenceScorer()
    confidence = scorer.calculate(observations, weights, context=None, critical_factors=[])
    
    # 全对齐，置信度应为 1.0
    assert confidence == pytest.approx(1.0)

def test_confidence_conflict_penalty():
    """测试冲突惩罚：当因子方向严重相反时，置信度应下降。"""
    observations = [
        FactorObservation(name="F1", score=8.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="F2", score=-8.0, is_valid=True, details={}, description="", timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
    ]
    weights = {"F1": 1.0, "F2": 1.0}
    scorer = ProbabilisticConfidenceScorer()
    confidence = scorer.calculate(observations, weights, context=None, critical_factors=[])
    
    # 冲突，置信度应远小于 1.0
    assert confidence < 0.7
