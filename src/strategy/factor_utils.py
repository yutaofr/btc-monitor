"""
Shared utilities for BTC Monitor V3.0 (TADR).
Ensures Bit-identical parity between live engine and backtest.
"""
from typing import Any

def quantize_score(val: Any, precision: int = 8) -> float:
    """
    指令 [4.1]：统一封装 8 位精度取整逻辑。
    使用 round() 确保浮点数在向量化计算与逐点计算中保持一致。
    """
    try:
        return round(float(val), precision)
    except (ValueError, TypeError):
        return 0.0

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """防止除零风险。"""
    if denominator == 0:
        return default
    return numerator / denominator
