"""
Shared utilities for BTC Monitor V3.0 (TADR).
Ensures Bit-identical parity between live engine and backtest.
"""
from typing import Any
from datetime import datetime, timezone

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

def check_freshness(ts: datetime, ttl_hours: int) -> bool:
    """
    指令 [2.1]：数据新鲜度校验。
    统一在 UTC 坐标系下运行。
    """
    if ts is None: return False
    # 确保 ts 是 offset-aware 的 UTC 时间
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    delta_hours = (now - ts).total_seconds() / 3600
    return delta_hours <= ttl_hours
