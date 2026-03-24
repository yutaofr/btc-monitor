from typing import Dict, List, Optional
from enum import Enum

class ConfidenceBucket(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class PositionCalibrator:
    """
    Handles confidence mapping for the Position Advisory branch.
    Mappings should ideally be loaded from historical backtest results.
    """
    def __init__(self):
        # Default buckets based on combined strategic agreement and tactical confirmation
        # These numbers are normalized to 0-100
        self.default_map = {
            "BULLISH_ACCUMULATION": {
                "low": 50,
                "medium": 65,
                "high": 80,
                "very_high": 95
            },
            "OVERHEATED": {
                "low": 50,
                "medium": 60,
                "high": 75,
                "very_high": 90
            },
            "NEUTRAL": {
                "neutral": 50
            }
        }

    def calibrate(self, regime: str, agreement_score: float, has_tactical_confirmation: bool) -> int:
        """
        Return a calibrated confidence score (0-100).
        """
        if regime not in self.default_map:
            return 50
            
        regime_map = self.default_map[regime]
        
        if regime == "NEUTRAL":
            return regime_map.get("neutral", 50)
            
        if agreement_score < 5.5:
            bucket = "low"
        elif agreement_score < 8.0:
            bucket = "medium" if not has_tactical_confirmation else "high"
        else:
            bucket = "high" if not has_tactical_confirmation else "very_high"
            
        return regime_map.get(bucket, 50)

class CashCalibrator:
    """
    Handles confidence mapping for the Incremental Cash Advisory branch.
    Timing-sensitive deployment mapping.
    """
    def __init__(self):
        self.default_map = {
            "BUY_NOW": {
                "low": 50,
                "medium": 70,
                "high": 85,
                "very_high": 98
            },
            "STAGGER_BUY": {
                "neutral": 50
            },
            "WAIT": {
                "neutral": 50
            }
        }

    def calibrate(self, action: str, agreement_score: float, has_tactical_confirmation: bool) -> int:
        if action not in self.default_map:
            return 50
            
        action_map = self.default_map[action]
        
        if action in ["STAGGER_BUY", "WAIT"]:
            return action_map.get("neutral", 50)
            
        # BUY_NOW confidence depends heavily on agreement and tactical alignment
        if agreement_score < 6.0:
            bucket = "low"
        elif agreement_score < 8.5:
            bucket = "medium" if not has_tactical_confirmation else "high"
        else:
            bucket = "high" if not has_tactical_confirmation else "very_high"
            
        return action_map.get(bucket, 50)
