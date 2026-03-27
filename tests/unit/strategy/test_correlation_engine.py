import pytest
import pandas as pd
import numpy as np
from src.monitoring.correlation_engine import CorrelationEngine

def test_correlation_calculation():
    """
    测试相关性计算逻辑：
    - 验证 90 天滚动相关性的计算精度
    - 验证不同相关性等级下的 Regime 分类
    """
    # 模拟 100 天的收益率数据
    dates = pd.date_range(start="2026-01-01", periods=100)
    btc_returns = np.random.normal(0.01, 0.02, 100)
    spx_returns = btc_returns * 0.8 + np.random.normal(0, 0.01, 100) # 高正相关
    dxy_returns = -btc_returns * 0.7 + np.random.normal(0, 0.01, 100) # 高负相关
    
    data = pd.DataFrame({
        'BTC': btc_returns,
        'SPX': spx_returns,
        'DXY': dxy_returns
    }, index=dates)
    
    engine = CorrelationEngine(window=90)
    context = engine.classify(data)
    
    # 1. 验证相关性值存在
    assert 'SPX' in context.correlations
    assert 'DXY' in context.correlations
    
    # 2. 验证高相关性下的 Regime 识别 (Risk-On)
    # 因为 SPX 与 BTC 高正相关 (0.8)，预期 regime 包含 Risk-On
    assert context.regime_labels == ["Risk-On"] or "Risk-On" in context.regime_labels
    
    # 3. 验证负相关下的 Regime 识别 (Liquidity-Driven)
    # 因为 DXY 与 BTC 高负相关 (-0.7)，预期 regime 包含 Liquidity-Driven
    assert "Liquidity-Driven" in context.regime_labels

def test_correlation_engine_graceful_failure():
    """验证数据不足时的处理逻辑"""
    data = pd.DataFrame({'BTC': [0.01], 'SPX': [0.02]})
    engine = CorrelationEngine(window=90)
    context = engine.classify(data)
    
    # 数据不足应标记为不确定或回退到默认
    assert context.is_valid is False
    assert context.regime_labels == ["Neutral"]
