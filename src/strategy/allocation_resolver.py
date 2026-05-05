import numpy as np
from src.config import Config

class AllocationResolver:
    """
    TADR Architecture: Allocation Layer
    Maps scores and confidence to a target allocation percentage.
    Uses a sigmoid function with adaptive slope (k) based on LTM precision.
    """

    def __init__(self, floor: float = None, cap: float = None, k_base: float = None, p_benchmark: float = None):
        # 使用配置类参数作为默认值 [指令 2.1]
        self.floor = floor if floor is not None else Config.TADR_ALLOCATION_FLOOR
        self.cap = cap if cap is not None else Config.TADR_ALLOCATION_CAP
        self.k_base = k_base if k_base is not None else Config.TADR_ALLOCATION_K_BASE
        self.p_benchmark = p_benchmark if p_benchmark is not None else Config.TADR_ALLOCATION_P_BENCHMARK
        self.theta = 0.0 # 中性偏移量

    def map_to_allocation(self, score: float, confidence: float, ltm_precision: float) -> float:
        """
        Input:
          score: Strategic total score (-10 to +10)
          confidence: Probabilistic confidence (0.0 to 1.0)
          ltm_precision: Last 12 Months Precision (0.0 to 1.0)
        Returns: Target Allocation % (0.0 to 1.0)
        """
        # 1. 计算自适应斜率 (Adaptive k)
        k = self.k_base * max(0.5, ltm_precision / self.p_benchmark)

        # 2. Sigmoid 映射 (Raw Signal to Range [0.0, 1.0])
        z = k * (score - self.theta)
        raw_alloc_factor = 1.0 / (1 + np.exp(-z))
        
        # 3. 计算基于分数的理论仓位
        theoretical_alloc = self.floor + (self.cap - self.floor) * raw_alloc_factor

        # 4. 置信度约束 (Confidence Scaling)
        # 核心：置信度直接缩放“超出底仓的溢价部分”
        # 当 confidence=1.0, alloc = theoretical_alloc
        # 当 confidence=0.0, alloc = Floor
        final_allocation = self.floor + (theoretical_alloc - self.floor) * confidence

        from src.strategy.factor_utils import quantize_score
        return float(np.clip(quantize_score(final_allocation), 0.0, 1.0))
