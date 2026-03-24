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
        blocked_reasons = []
        
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

        # Calculate Total Strategic Strength
        raw_blocks = {}
        for obs in observations:
            try:
                defn = get_factor(obs.name)
                if defn.layer == Layer.STRATEGIC.value and obs.is_valid:
                    if defn.block not in raw_blocks:
                        raw_blocks[defn.block] = []
                    raw_blocks[defn.block].append(obs.score)
            except KeyError: continue
            
        block_means = []
        for scores in raw_blocks.values():
            if scores:
                block_means.append(sum(scores) / len(scores))
        
        agreement_weight = sum(abs(s) for s in block_means)

        if regime == StrategicRegime.BULLISH_ACCUMULATION:
            action = Action.ADD
            confidence = 70
            summary = "High-confidence bullish accumulation regime confirmed."
            
            # Opportunity Gap / Evidence Overload: If Valuation and Trend are extreme, Macro panic is secondary
            is_evidence_overload = False
            try:
                val_obs = [o for o in observations if o.is_valid and get_factor(o.name).block == "valuation"]
                trd_obs = [o for o in observations if o.is_valid and get_factor(o.name).block == "trend_cycle"]
                valuation_score = sum(o.score * get_factor(o.name).default_weight for o in val_obs)
                trend_score = sum(o.score * get_factor(o.name).default_weight for o in trd_obs)
                if valuation_score > 12.0 and trend_score > 5.0:
                    is_evidence_overload = True
            except: pass

            if tactical_info["tactical_bias"] == "BULLISH_CONFIRMED":
                confidence += 20
            elif tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                action = Action.HOLD 
                confidence = 50
                summary = "Tactical setup is bearishly overstretched; holding despite bullish regime."
                blocked_reasons.append("Tactical Bearish Conflict")

            # Gating: Selective but reachable (Threshold 5.0 or Overload)
            if action == Action.ADD and agreement_weight < 5.0 and not is_evidence_overload: 
                action = Action.HOLD
                summary = "Strategic strength is insufficient for high-confidence ADD."
                blocked_reasons.append(f"Low Agreement ({agreement_weight:.1f})")

        elif regime == StrategicRegime.OVERHEATED:
            action = Action.REDUCE
            confidence = 70
            summary = "Market showing signs of cyclical overheating."
            
            # Gating: Selective but reachable (Threshold 5.0)
            if agreement_weight < 5.0: 
                action = Action.HOLD
                summary = "Strategic strength is insufficient for high-confidence REDUCE."
                blocked_reasons.append(f"Low Agreement ({agreement_weight:.1f})")
            
            # Cyclic Breakdown Confirmation (EMA21) - confirmed filter
            ema21_obs = next((o for o in observations if o.name == "EMA21_Weekly"), None)
            if ema21_obs and ema21_obs.is_valid:
                rel_dist = ema21_obs.details.get("rel_dist", 1.0)
                if rel_dist > 0.0: # Price must be below EMA to confirm breakdown
                    action = Action.HOLD
                    confidence = 50
                    summary = "Strategic overheating detected, but price has not definitively broken 21w EMA support."
                    blocked_reasons.append(f"EMA21 Support Holding ({rel_dist:+.1%})")

            # Tactical Requirement: Must not be strongly bullish
            if tactical_info["tactical_bias"] == "BULLISH_CONFIRMED":
                action = Action.HOLD 
                confidence = 50
                summary = "Tactical momentum is still strongly bullish; holding despite overheating signs."
                blocked_reasons.append("Tactical Bullish Conflict")
            elif tactical_info["tactical_bias"] == "NEUTRAL" and action == Action.REDUCE:
                confidence = 60 # Lower confidence if not bearish confirmed
            elif tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                confidence += 30

        # ABSOLUTE NO-CONFLICT GATE: If any decisional factor strongly contradicts the action
        for o in observations:
            if not o.is_valid: continue
            try:
                defn = get_factor(o.name)
                if defn.layer == Layer.RESEARCH.value: continue # Research doesn't block

                if action == Action.ADD and o.score < -5.0:
                    if o.name == "EMA21_Weekly": continue # Low EMA21 is expected at bottom
                    if defn.block == "macro_liquidity": continue # Macro panic shouldn't veto deep value
                    action = Action.HOLD
                    confidence = 50
                    summary = f"Action ADD blocked by significant conflicting evidence: {o.name} ({o.score})"
                    blocked_reasons.append(f"Veto: {o.name}")
                    break
                if action == Action.REDUCE and o.score > 2.0:
                    # BLOCK NAME CHECK: Ensure it matches factor_registry.py
                    if defn.block in ["trend_cycle", "macro_liquidity"]: continue 
                    if defn.layer == Layer.TACTICAL.value: continue # Don't let noisy tactical sentiment block a cyclic exit
                    action = Action.HOLD
                    confidence = 50
                    summary = f"Action REDUCE blocked by significant conflicting evidence: {o.name} ({o.score})"
                    blocked_reasons.append(f"Veto: {o.name}")
                    break
            except: continue

        # Supporting/Conflicting/Research Lists
        supporting: List[str] = []
        conflicting: List[str] = []
        research: List[str] = []
        
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
            blocked_reasons=blocked_reasons,
            freshness_warnings=warnings,
            excluded_research_factors=research,
            summary=summary
        )
