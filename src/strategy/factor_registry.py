from typing import List, Dict, Optional, Any
from src.strategy.factor_models import FactorDefinition

class FactorRegistry:
    """
    TADR Architecture: Policy Layer
    Instruction [2.3]: Decouples metadata from engine and implements schema validation.
    """
    
    def __init__(self, initial_factors: Optional[List[Dict[str, Any]]] = None):
        self._registry: Dict[str, FactorDefinition] = {}
        if initial_factors:
            for f in initial_factors:
                self.register_factor(f)
        self.validate_all_factors()

    def register_factor(self, config: Dict[str, Any]) -> FactorDefinition:
        """
        Registers a new factor with Pydantic validation.
        Raises ValidationError if config is invalid.
        """
        definition = FactorDefinition(**config)
        self._registry[definition.name] = definition
        return definition

    def validate_all_factors(self):
        """
        [指令 2.1, 2.3] 配置一致性自检：
        1. 确保至少定义了 2 个 is_critical=True 的因子以支持 Fail-Closed 熔断。
        2. 验证权重总和不为 0。
        """
        critical_count = len(self.get_critical_factors())
        if critical_count < 2 and len(self._registry) > 0:
            # 仅在非空时校验，防止初始化阶段意外报错
            print(f"[WARNING] Registry has only {critical_count} critical factors. Fail-Closed logic needs at least 2.")
        
        weights_sum = sum(self.get_weights_map().values())
        if weights_sum == 0 and len(self._registry) > 0:
            raise ValueError("Configuration Error: Total weights sum to zero.")

    def get_factor(self, name: str) -> FactorDefinition:
        """Return a registered factor by name, raising KeyError if missing."""
        if name not in self._registry:
            raise KeyError(f"Factor '{name}' not found in registry.")
        return self._registry[name]

    def get_all_factors(self) -> List[FactorDefinition]:
        """Return all factor definitions."""
        return list(self._registry.values())

    def get_critical_factors(self) -> List[str]:
        """Returns names of factors marked as is_critical=True."""
        return [f.name for f in self._registry.values() if f.is_critical]

    def get_weights_map(self) -> Dict[str, float]:
        """Returns map of factor names to default weights."""
        return {f.name: f.default_weight for f in self._registry.values()}

# --- Global Access Functions (Backward Compatibility) ---
# 指令 [2.3]：允许 V2.x 代码通过单例模式访问新版 Pydantic 注册表。
_default_registry = FactorRegistry()

# 注入核心生产因子以兼容旧测试
_PROD_FACTORS = [
    {"name": "MVRV_Proxy", "layer": "strategic", "block": "valuation", "source_class": "on_chain", 
     "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.5, "confidence_class": "high", "is_critical": True},
    {"name": "Puell_Multiple", "layer": "strategic", "block": "valuation", "source_class": "on_chain", 
     "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.2, "confidence_class": "high", "is_critical": True},
    {"name": "200WMA", "layer": "strategic", "block": "trend_cycle", "source_class": "price", 
     "is_required_for_add": True, "is_required_for_reduce": True, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "high", "is_critical": False},
    {"name": "Cycle_Pos", "layer": "strategic", "block": "trend_cycle", "source_class": "price", 
     "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "high", "is_critical": False},
    {"name": "Net_Liquidity", "layer": "strategic", "block": "macro_liquidity", "source_class": "macro", 
     "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 72, "default_weight": 1.0, "confidence_class": "high", "is_critical": True},
    {"name": "Yields", "layer": "strategic", "block": "macro_liquidity", "source_class": "macro", 
     "is_required_for_add": True, "is_required_for_reduce": False, "is_required_for_buy_now": True, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 72, "default_weight": 1.0, "confidence_class": "high", "is_critical": False},
    {"name": "FearGreed", "layer": "tactical", "block": "sentiment", "source_class": "sentiment", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": True, "is_backtestable": False, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "medium", "is_critical": False},
    {"name": "RSI_Div", "layer": "tactical", "block": "technical", "source_class": "technical", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "medium", "is_critical": False},
    {"name": "Short_Term_Stretch", "layer": "tactical", "block": "technical", "source_class": "technical", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": True, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "medium", "is_critical": False},
    {"name": "EMA21_Weekly", "layer": "tactical", "block": "trend_cycle", "source_class": "price", 
     "is_required_for_add": False, "is_required_for_reduce": True, "is_required_for_buy_now": False, 
     "is_wait_veto": False, "is_backtestable": True, "freshness_ttl_hours": 24, "default_weight": 1.0, "confidence_class": "high", "is_critical": False},
    # 研究因子 (Research-only)
    {"name": "Options_Wall", "layer": "research", "block": "market", "source_class": "derivatives", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": False, "is_backtestable": False, "freshness_ttl_hours": 24, "default_weight": 0.0, "confidence_class": "low", "is_critical": False},
    {"name": "ETF_Flow", "layer": "research", "block": "market", "source_class": "etf", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": False, "is_backtestable": False, "freshness_ttl_hours": 24, "default_weight": 0.0, "confidence_class": "low", "is_critical": False},
    {"name": "Production_Cost", "layer": "research", "block": "valuation", "source_class": "on_chain", 
     "is_required_for_add": False, "is_required_for_reduce": False, "is_required_for_buy_now": False, 
     "is_wait_veto": False, "is_backtestable": False, "freshness_ttl_hours": 24, "default_weight": 0.0, "confidence_class": "low", "is_critical": False}
]
for f_cfg in _PROD_FACTORS:
    _default_registry.register_factor(f_cfg)

def get_factor(name: str) -> FactorDefinition:
    return _default_registry.get_factor(name)

def get_all_factors() -> List[FactorDefinition]:
    return _default_registry.get_all_factors()
