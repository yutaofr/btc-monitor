import pytest
from datetime import datetime, timezone
from src.strategy.tadr_engine import TADREngine
from src.strategy.factor_models import FactorObservation, Action
from src.monitoring.correlation_engine import CorrelationContext

def create_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name, score=score, is_valid=is_valid, details={}, description="",
        timestamp=datetime.now(timezone.utc), freshness_ok=True, confidence_penalty=0.0, blocked_reason=""
    )

def test_scenario_full_bullish_accumulation():
    """场景 1：高覆盖率看多 (确认 ADD 指令)"""
    engine = TADREngine()
    # 提供几乎全量的因子以获得高置信度
    obs = [
        create_obs("MVRV_Proxy", 10.0),
        create_obs("Puell_Multiple", 10.0),
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0),
        create_obs("Yields", 10.0),
        create_obs("Cycle_Pos", 10.0),
        create_obs("FearGreed", 10.0),
        create_obs("RSI_Weekly", 10.0)
    ]
    rec = engine.evaluate(obs)
    # 期望：在充足证据下触发 ADD
    assert rec.action == Action.ADD.value
    assert rec.confidence > 50  # V3 置信度通常比 V2 更保守

def test_scenario_aggressive_overheated():
    """场景 2：证据充分的过热 (确认 REDUCE 指令)"""
    engine = TADREngine()
    # 必须有足够多的因子给出负分，才能穿透全权重归一化达到 -3.5 以下
    obs = [
        create_obs("MVRV_Proxy", -10.0),
        create_obs("Puell_Multiple", -10.0),
        create_obs("200WMA", -10.0),
        create_obs("Cycle_Pos", -10.0),
        create_obs("Net_Liquidity", -10.0),
        create_obs("Yields", -10.0),
        create_obs("Short_Term_Stretch", -10.0),
        create_obs("EMA21_Weekly", -10.0)
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.REDUCE.value
    assert "Market Overheated" in rec.summary

def test_scenario_fail_closed_critical_missing():
    """场景 3：熔断机制 (核心因子不可用)"""
    engine = TADREngine()
    # 虽然其他因子看多，但 MVRV_Proxy 这种 is_critical=True 的因子缺失应锁死系统
    obs = [
        create_obs("MVRV_Proxy", 0.0, is_valid=False), 
        create_obs("200WMA", 10.0),
        create_obs("Net_Liquidity", 10.0)
    ]
    rec = engine.evaluate(obs)
    assert rec.action == Action.INSUFFICIENT_DATA.value
    assert "SYSTEM_GATE_LOCKED" in rec.summary

def test_correlation_weight_drift_impact():
    """场景 4：动态相关性对决策的微调"""
    engine = TADREngine()
    # 以流动性因子为例
    obs = [
        create_obs("MVRV_Proxy", 5.0),
        create_obs("Puell_Multiple", 5.0),
        create_obs("200WMA", 5.0),
        create_obs("Net_Liquidity", 10.0), # 极强流动性
        create_obs("Yields", 5.0),
        create_obs("Cycle_Pos", 5.0)
    ]
    
    # 1. 低相关性 (rho=0.1)
    ctx_low = CorrelationContext(correlations={"Net_Liquidity": 0.1}, regime_labels=["Neutral"], is_valid=True)
    rec_low = engine.evaluate(obs, context=ctx_low)
    
    # 2. 高相关性 (rho=0.9, 流动性权重增加)
    ctx_high = CorrelationContext(correlations={"Net_Liquidity": 0.9}, regime_labels=["Liquidity-Driven"], is_valid=True)
    rec_high = engine.evaluate(obs, context=ctx_high)
    
    # 验证：高相关性下，该因子在 norm_score 中贡献更大，目标仓位应有所变化
    # 由于得分全是正的，高权重会推高 norm_score -> 进而可能推高 target_allocation
    assert rec_high.confidence >= rec_low.confidence
