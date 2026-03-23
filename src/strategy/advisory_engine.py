from typing import List
from datetime import datetime
from src.strategy.factor_models import FactorObservation, Recommendation, Action, Layer
from src.strategy.factor_registry import get_factor
from src.strategy.strategic_engine import StrategicEngine, StrategicRegime
from src.strategy.tactical_engine import TacticalEngine

class AdvisoryEngine:
    """
    Coordinates strategic and tactical analysis to provide high-confidence advice.
    """
    def __init__(self):
        self.strategic_engine = StrategicEngine()
        self.tactical_engine = TacticalEngine()

    def evaluate(self, observations: List[FactorObservation]) -> Recommendation:
        # 1. Infer Strategic Regime
        regime = self.strategic_engine.infer_regime(observations)
        
        # 2. Evaluate Tactical Evidence
        tactical_info = self.tactical_engine.evaluate_tactical(observations)
        
        # 3. Decision Logic & Gating
        action = Action.HOLD
        confidence = 50
        summary = "Market is in a neutral or transitional phase."
        
        if regime == StrategicRegime.INSUFFICIENT_DATA:
            return Recommendation(
                action=Action.INSUFFICIENT_DATA.value,
                confidence=50,
                strategic_regime=StrategicRegime.INSUFFICIENT_DATA.value,
                tactical_state=tactical_info["tactical_bias"],
                supporting_factors=[],
                conflicting_factors=[],
                missing_required_blocks=["macro_liquidity", "valuation", "trend_cycle"],
                missing_required_factors=[],
                blocked_reasons=["Strategic blocks are incomplete."],
                freshness_warnings=[],
                excluded_research_factors=[],
                summary="Missing required strategic evidence to form a high-confidence view."
            )

        if regime == StrategicRegime.BULLISH_ACCUMULATION:
            action = Action.ADD
            confidence = 70 # Base confidence for 3-block proof
            summary = "High-confidence bullish accumulation regime confirmed by Valuation, Trend, and Macro blocks."
            
            # Tactical boost or penalty
            if tactical_info["tactical_bias"] == "BULLISH_CONFIRMED":
                confidence += 15
                summary += " Tactical setup is also bullish."
            elif tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                confidence -= 20
                summary += " WARNING: Tactical setup is bearishly overstretched."
                action = Action.HOLD # Fail closed on conflict

        elif regime == StrategicRegime.OVERHEATED:
            action = Action.REDUCE
            confidence = 70
            summary = "Market showing signs of cyclical overheating across multiple blocks."
            
            if tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                confidence += 20
                summary += " Tactical indicators confirm reversal risk."
            elif tactical_info["tactical_bias"] == "BULLISH_CONFIRMED":
                confidence -= 30
                summary += " Tactical momentum is still strong; reducing with caution."

        # Supporting/Conflicting/Research Lists
        supporting = []
        conflicting = []
        research = []
        
        for o in observations:
            try:
                defn = get_factor(o.name)
                if defn.layer == Layer.RESEARCH.value:
                    research.append(o.name)
                    continue
                
                if not o.is_valid:
                    continue
                    
                if action == Action.ADD:
                    if o.score > 0: supporting.append(o.name)
                    elif o.score < 0: conflicting.append(o.name)
                elif action == Action.REDUCE:
                    if o.score < 0: supporting.append(o.name)
                    elif o.score > 0: conflicting.append(o.name)
            except KeyError:
                continue

        # Freshness Warnings
        warnings = [f"{o.name} is stale" for o in observations if not o.freshness_ok]

        return Recommendation(
            action=action.value,
            confidence=min(100, max(0, confidence)),
            strategic_regime=regime.value,
            tactical_state=tactical_info["tactical_bias"],
            supporting_factors=supporting[:5],
            conflicting_factors=conflicting[:5],
            missing_required_blocks=[],
            missing_required_factors=[],
            blocked_reasons=[],
            freshness_warnings=warnings,
            excluded_research_factors=research,
            summary=summary
        )
