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
        """Return all registered factors."""
        return list(self._registry.values())

    def get_critical_factors(self) -> List[str]:
        """Returns names of factors marked as is_critical=True."""
        return [f.name for f in self._registry.values() if f.is_critical]

    def get_weights_map(self) -> Dict[str, float]:
        """Returns map of factor names to default weights."""
        return {f.name: f.default_weight for f in self._registry.values()}
