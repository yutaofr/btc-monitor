import numpy as np

class AllocationResolver:
    """
    TADR Architecture: Allocation Layer
    Maps scores and confidence to a target allocation percentage.
    Uses a sigmoid function with adaptive slope (k) based on LTM precision.
    """

    def __init__(self, floor: float = 0.2, cap: float = 0.8, k_base: float = 1.2, p_benchmark: float = 0.85):
        self.floor = floor
        self.cap = cap
        self.k_base = k_base
        self.p_benchmark = p_benchmark
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

        return float(np.clip(final_allocation, 0.0, 1.0))
