import pytest
from pydantic import ValidationError
from src.strategy.factor_registry import FactorRegistry

def test_factor_registry_schema_validation():
    """
    指令 [2.3] 验证：非法的权重或类型应触发 ValidationError。
    """
    registry = FactorRegistry()
    
    # 1. 测试权重越界 (> 10.0)
    with pytest.raises(ValidationError):
        registry.register_factor({
            "name": "Invalid_Weight",
            "layer": "strategic",
            "block": "valuation",
            "source_class": "price",
            "is_required_for_add": True,
            "is_required_for_reduce": True,
            "is_required_for_buy_now": True,
            "is_wait_veto": False,
            "is_backtestable": True,
            "freshness_ttl_hours": 48,
            "default_weight": 25.0, # Illegal!
            "confidence_class": "high"
        })

    # 2. 测试缺失必要字段
    with pytest.raises(ValidationError):
        registry.register_factor({
            "name": "Missing_Field",
            "layer": "strategic"
            # block missing
        })

def test_factor_registry_is_critical_flag():
    """
    验证 V3 特有的 is_critical 标志。
    """
    registry = FactorRegistry()
    registry.register_factor({
        "name": "MVRV_Proxy",
        "layer": "strategic",
        "block": "valuation",
        "source_class": "on_chain",
        "is_required_for_add": True,
        "is_required_for_reduce": False,
        "is_required_for_buy_now": True,
        "is_wait_veto": False,
        "is_backtestable": True,
        "freshness_ttl_hours": 48,
        "default_weight": 1.5,
        "confidence_class": "low",
        "is_critical": True # V3 Feature
    })
    
    factor = registry.get_factor("MVRV_Proxy")
    assert factor.is_critical is True
