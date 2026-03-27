import pytest
import numpy as np
from datetime import datetime
from src.strategy.factor_models import FactorObservation
from src.strategy.probabilistic_confidence_scorer import ProbabilisticConfidenceScorer
from src.monitoring.correlation_engine import CorrelationContext

def test_redundancy_smooth_transition():
    """
    指令 [2.1] 验证：冗余压制必须是平滑的，不能有断崖式跳变。
    验证相关性从 0.79 变到 0.81 时，置信度的变化是微小的。
    """
    scorer = ProbabilisticConfidenceScorer()
    weights = {"SPX_Proxy": 1.0, "BTC_Trend": 1.0}
    observations = [
        FactorObservation(name="SPX_Proxy", score=10.0, is_valid=True, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="BTC_Trend", score=10.0, is_valid=True, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
    ]

    # 1. 相关性 0.79
    ctx_79 = CorrelationContext(correlations={"SPX": 0.79}, regime_labels=["Risk-On"], is_valid=True)
    conf_79 = scorer.calculate(observations, weights, ctx_79, critical_factors=[])

    # 2. 相关性 0.81
    ctx_81 = CorrelationContext(correlations={"SPX": 0.81}, regime_labels=["Risk-On"], is_valid=True)
    conf_81 = scorer.calculate(observations, weights, ctx_81, critical_factors=[])

    # 验证平滑度：变化不应超过 5% (阶梯函数会导致 20% 的跳变)
    diff = abs(conf_79 - conf_81)
    assert diff < 0.05, f"Jitter detected: diff={diff}"
    # 且 0.81 时的置信度应略低于 0.79
    assert conf_81 < conf_79
