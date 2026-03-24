"""
Branch-specific confidence calibrators for the dual-decision advisory system.
"""
from typing import Dict


class PositionCalibrator:
    """
    Handles confidence mapping for the Position Advisory branch.
    Scores are derived from the combination of strategic agreement weight and
    tactical confirmation. Thresholds should be revisited after each major backtest run.
    """
    _default_map: Dict[str, Dict[str, int]] = {
        "BULLISH_ACCUMULATION": {"low": 50, "medium": 65, "high": 80, "very_high": 95},
        "OVERHEATED":           {"low": 50, "medium": 60, "high": 75, "very_high": 90},
        "NEUTRAL":              {"neutral": 50},
    }

    def calibrate(self, regime: str, agreement_score: float, has_tactical_confirmation: bool) -> int:
        """Return a calibrated confidence score (0-100)."""
        regime_map = self._default_map.get(regime)
        if regime_map is None:
            return 50
        if regime == "NEUTRAL":
            return regime_map["neutral"]
        bucket = self._bucket(agreement_score, has_tactical_confirmation)
        return regime_map.get(bucket, 50)

    @staticmethod
    def _bucket(agreement_score: float, has_tactical_confirmation: bool) -> str:
        if agreement_score < 5.5:
            return "low"
        if agreement_score < 8.0:
            return "high" if has_tactical_confirmation else "medium"
        return "very_high" if has_tactical_confirmation else "high"


class CashCalibrator:
    """
    Handles confidence mapping for the Incremental Cash Advisory branch.
    STAGGER_BUY now receives a scaled confidence based on strategic strength,
    rather than a flat 50, to better represent how compelling the underlying setup is.
    """
    _buy_now_map: Dict[str, int] = {"low": 50, "medium": 70, "high": 85, "very_high": 98}
    _stagger_map: Dict[str, int] = {"low": 45, "medium": 55, "high": 60}

    def calibrate(self, action: str, agreement_score: float, has_tactical_confirmation: bool) -> int:
        """Return a calibrated confidence score (0-100)."""
        if action == "BUY_NOW":
            bucket = self._bucket(agreement_score, has_tactical_confirmation)
            return self._buy_now_map.get(bucket, 50)
        if action == "STAGGER_BUY":
            # Scaled: even in a veto, stronger strategic evidence = higher confidence
            stagger_bucket = "high" if agreement_score >= 8.0 else ("medium" if agreement_score >= 5.5 else "low")
            return self._stagger_map.get(stagger_bucket, 50)
        # WAIT
        return 50

    @staticmethod
    def _bucket(agreement_score: float, has_tactical_confirmation: bool) -> str:
        if agreement_score < 6.0:
            return "low"
        if agreement_score < 8.5:
            return "high" if has_tactical_confirmation else "medium"
        return "very_high" if has_tactical_confirmation else "high"
