import pytest
from datetime import datetime
from src.strategy.factor_models import FactorObservation
from src.strategy.probabilistic_confidence_scorer import ProbabilisticConfidenceScorer
from src.monitoring.correlation_engine import CorrelationContext

def test_fail_closed_critical_missing():
    """
    指令 [2.2] 验证：缺失核心因子（Macro & Valuation）时，系统必须 Fail-Closed。
    预期置信度 C 强制降为 0，导致仓位回归 Floor。
    """
    observations = [
        # Macro 缺失 (Invalid)
        FactorObservation(name="Net_Liquidity", score=0.0, is_valid=False, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=False, confidence_penalty=1.0, blocked_reason=""),
        # Valuation 缺失 (Invalid)
        FactorObservation(name="MVRV_Proxy", score=0.0, is_valid=False, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=False, confidence_penalty=1.0, blocked_reason=""),
        # 其他因子强看多
        FactorObservation(name="RSI_Div", score=10.0, is_valid=True, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
    ]
    
    weights = {"Net_Liquidity": 2.0, "MVRV_Proxy": 2.0, "RSI_Div": 1.0}
    scorer = ProbabilisticConfidenceScorer()
    
    # 注入 Context (假设正常)
    context = CorrelationContext(correlations={}, regime_labels=["Neutral"], is_valid=True)
    
    confidence = scorer.calculate(observations, weights, context)
    
    # 因为核心因子全丢，置信度必须为 0 (Fail-Closed)
    assert confidence == 0.0

def test_factor_redundancy_penalty():
    """
    指令 [2.2 建议]：相关性过高时，降低冗余因子权重。
    """
    observations = [
        FactorObservation(name="SPX_Proxy", score=10.0, is_valid=True, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
        FactorObservation(name="BTC_Trend", score=10.0, is_valid=True, details={}, description="", 
                          timestamp=datetime.now(), freshness_ok=True, confidence_penalty=1.0, blocked_reason=""),
    ]
    weights = {"SPX_Proxy": 1.0, "BTC_Trend": 1.0}
    
    scorer = ProbabilisticConfidenceScorer()
    
    # 模拟极高相关性 (SPX 与 BTC 高度同步)
    context = CorrelationContext(correlations={"SPX": 0.95}, regime_labels=["Risk-On"], is_valid=True)
    
    # 计算带相关性惩罚的置信度
    confidence = scorer.calculate(observations, weights, context)
    
    # 由于冗余，置信度应被压制，不应为 1.0
    assert confidence < 0.9
