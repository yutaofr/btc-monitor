import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.strategy.live_data_provider import LiveDataProvider
from src.strategy.tadr_engine import TADREngine
from src.strategy.reporting import TADRReporter
from src.strategy.factor_models import FactorObservation
from src.strategy.factor_registry import FactorRegistry
from datetime import datetime

def test_full_cycle_normal_with_redundancy():
    """
    场景 1：正常运行且触发冗余压制。
    """
    mock_binance = MagicMock()
    mock_fred = MagicMock()
    
    dates = pd.date_range(end="2026-03-27", periods=100)
    mock_binance.fetch_ohlcv.return_value = pd.DataFrame({'close': [60000]*100}, index=dates)
    mock_fred.get_series.side_effect = [
        pd.Series([100.0]*100, index=dates),
        pd.Series([5000.0]*100, index=dates)
    ]
    
    # 注入配置好的 Registry
    registry = FactorRegistry()
    factors = [
        {"name": "Net_Liquidity", "layer": "strategic", "block": "macro", "source_class": "macro", 
         "is_required_for_add": True, "is_required_for_reduce": True, "is_required_for_buy_now": True,
         "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, 
         "confidence_class": "high", "is_critical": True},
        {"name": "SPX_Proxy", "layer": "strategic", "block": "market", "source_class": "price", 
         "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False,
         "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, 
         "confidence_class": "high", "is_critical": False}
    ]
    for f in factors: registry.register_factor(f)

    engine = TADREngine(registry=registry)
    reporter = TADRReporter()
    
    obs = [
        FactorObservation("Net_Liquidity", 5.0, True, {}, "", datetime.now(), True, 1.0, ""),
        FactorObservation("SPX_Proxy", 10.0, True, {}, "", datetime.now(), True, 1.0, ""),
        FactorObservation("BTC_Trend", 10.0, True, {}, "", datetime.now(), True, 1.0, ""),
    ]
    
    from src.monitoring.correlation_engine import CorrelationContext
    ctx = CorrelationContext({"SPX": 0.9}, ["Risk-On"], True)
    
    rec = engine.evaluate(obs, context=ctx)
    state = engine.last_internal_state
    report_md = reporter.generate_report_markdown(rec, state)
    
    # 验证 Multiplier 被压制 (0.9 corr -> ~0.673 multiplier)
    assert "**0.6730**" in report_md
    assert "Strategic Metrics" in report_md

def test_full_cycle_circuit_breaker():
    """
    场景 3：熔断状态。
    指令 [2.2] 验证：缺失 2 个核心因子必须触发 SYSTEM GATE LOCKED。
    """
    # 注入包含关键因子定义的 Registry
    registry = FactorRegistry()
    registry.register_factor({
        "name": "Net_Liquidity", "layer": "strategic", "block": "macro", "source_class": "macro", 
        "is_required_for_add": True, "is_required_for_reduce": True, "is_required_for_buy_now": True,
        "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, 
        "confidence_class": "high", "is_critical": True
    })
    registry.register_factor({
        "name": "MVRV_Proxy", "layer": "strategic", "block": "valuation", "source_class": "on_chain", 
        "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True,
        "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, 
        "confidence_class": "high", "is_critical": True
    })

    engine = TADREngine(registry=registry)
    reporter = TADRReporter()
    
    # 模拟 2 个核心因子全失效
    obs = [
        FactorObservation("Net_Liquidity", 0.0, False, {}, "", datetime.now(), False, 1.0, ""),
        FactorObservation("MVRV_Proxy", 0.0, False, {}, "", datetime.now(), False, 1.0, ""),
    ]
    
    rec = engine.evaluate(obs)
    state = engine.last_internal_state
    report_md = reporter.generate_report_markdown(rec, state)
    
    # 验收标准
    assert "SYSTEM GATE LOCKED" in report_md
    assert "❌ MISSING" in report_md
    assert "Root Cause Analysis" in report_md
