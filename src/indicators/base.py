from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class IndicatorResult:
    name: str
    score: float       # Normalized score [-10, 10]
    weight: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

def calculate_rsi(series, period=14):
    """Utility to calculate RSI for a given series."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
