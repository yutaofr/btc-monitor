import pytest
from src.strategy.allocation_resolver import AllocationResolver

def test_allocation_mapping_neutral():
    """测试中性信号：分数为 0 时，仓位应接近 Floor (20%)。"""
    resolver = AllocationResolver(floor=0.2, cap=0.8, k_base=1.2)
    # Score=0, Confidence=1.0, Precision=0.85 (Benchmark)
    alloc = resolver.map_to_allocation(score=0.0, confidence=1.0, ltm_precision=0.85)
    
    # 预期在中点附近
    assert 0.2 < alloc < 0.6

def test_allocation_extreme_bull_high_confidence():
    """测试极强看多 + 高置信度：应接近上限。"""
    resolver = AllocationResolver(floor=0.2, cap=0.8, k_base=1.2)
    # Score=10.0 (Max), Confidence=1.0, Precision=0.85
    alloc = resolver.map_to_allocation(score=10.0, confidence=1.0, ltm_precision=0.85)
    
    # 预期接近 0.8
    assert 0.7 < alloc <= 0.8

def test_allocation_probabilistic_decline():
    """测试概率定价：当置信度下降时，即使信号强，仓位也应下降。"""
    resolver = AllocationResolver(floor=0.2, cap=0.8, k_base=1.2)
    
    # 高置信度 (1.0)
    alloc_high = resolver.map_to_allocation(score=10.0, confidence=1.0, ltm_precision=0.85)
    # 低置信度 (0.5)
    alloc_low = resolver.map_to_allocation(score=10.0, confidence=0.5, ltm_precision=0.85)
    
    assert alloc_low < alloc_high
    # 预期低置信度下的 10 分，应显著压低
    assert alloc_low < 0.6

def test_adaptive_k_slope():
    """测试自适应斜率：当 Precision 下降时，系统应更保守。"""
    resolver = AllocationResolver(floor=0.2, cap=0.8, k_base=2.0)
    
    # 信号 Score=3.0 (温和看多)
    # 表现优秀 (Precision=0.9) -> k 更陡 -> 仓位更高
    alloc_confident = resolver.map_to_allocation(score=3.0, confidence=1.0, ltm_precision=0.9)
    # 表现糟糕 (Precision=0.6) -> k 更缓 -> 仓位更低（向底仓回归）
    alloc_conservative = resolver.map_to_allocation(score=3.0, confidence=1.0, ltm_precision=0.6)
    
    assert alloc_conservative < alloc_confident
