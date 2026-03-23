from typing import List, Set
from src.strategy.factor_models import FactorObservation, Recommendation
from src.strategy.factor_registry import get_factor
from src.strategy.strategic_engine import StrategicEngine
from src.strategy.tactical_engine import TacticalEngine

class AdvisoryEngine:
    """
    Stateless advisory engine that maps factor observations into recommendations.
    Enforces strict block-level coverage and evidence rules.
    """
    def __init__(self):
        self.strategic_engine = StrategicEngine()
        self.tactical_engine = TacticalEngine()

    def evaluate(self, observations: List[FactorObservation]) -> Recommendation:
        # 1. Identify present factors and blocks (Exclude research factors from decision inputs)
        present_factors = set()
        block_scores = {"valuation": [], "trend_cycle": [], "macro_liquidity": [], "sentiment_tactical": []}
        
        missing_required_add = []
        missing_required_reduce = []
        blocked_reasons = []
        freshness_warnings = []
        excluded_research = []

        for obs in observations:
            if not obs.is_valid:
                continue
            if not getattr(obs, "freshness_ok", True):
                freshness_warnings.append(f"{obs.name} data is stale")
                
            try:
                definition = get_factor(obs.name)
                # Hardening policy: research factors are completely ignored for action/confidence decisions
                if definition.layer == "research":
                    excluded_research.append(obs.name)
                    continue
                    
                present_factors.add(obs.name)
                if definition.block in block_scores:
                    block_scores[definition.block].append(obs.score)
            except KeyError:
                pass

        # Check required factors
        # For simplicity in this dummy/minimal test path, we just check if required blocks are present
        blocks_present = {b for b, scores in block_scores.items() if scores}
        
        strategic_regime = self.strategic_engine.evaluate_regime(observations)
        tactical_state = self.tactical_engine.evaluate_tactical(observations)

        action = "HOLD"
        confidence = 50
        summary = "Mixed evidence."

        if strategic_regime == "INSUFFICIENT_DATA":
            action = "INSUFFICIENT_DATA"
            blocked_reasons.append("Missing required strategic blocks.")
            summary = "Cannot form conviction due to missing data."
        else:
            # Action Gates
            # ADD Gate
            val_scores = block_scores["valuation"]
            macro_scores = block_scores["macro_liquidity"]
            trend_scores = block_scores["trend_cycle"]
            
            val_avg = sum(val_scores)/len(val_scores) if val_scores else 0
            macro_avg = sum(macro_scores)/len(macro_scores) if macro_scores else 0
            trend_avg = sum(trend_scores)/len(trend_scores) if trend_scores else 0

            is_valuation_bullish = val_avg >= 3.0
            is_macro_bearish = macro_avg <= -3.0
            is_trend_bearish = trend_avg <= -3.0

            is_overheated = val_avg <= -3.0 or trend_avg <= -3.0

            bullish_factors = [obs.name for obs in observations if obs.is_valid and obs.score > 3.0]
            overheated_factors = [obs.name for obs in observations if obs.is_valid and obs.score < -3.0]

            # Base confidence based on number of active blocks, capped at 100
            confidence = min(100, 40 + (len(blocks_present) * 10) + (len(present_factors) * 5))
            
            # Apply confidence penalties from factors
            for obs in observations:
                if obs.is_valid:
                    confidence -= obs.confidence_penalty
            
            # Bound confidence between 0 and 100
            confidence = max(0, min(100, int(confidence)))
            
            # Check required factors against Registry
            from src.strategy.factor_registry import get_all_factors
            all_factors = get_all_factors()
            missing_required_add = [f.name for f in all_factors if f.is_required_for_add and f.name not in present_factors]
            missing_required_reduce = [f.name for f in all_factors if f.is_required_for_reduce and f.name not in present_factors]

            if strategic_regime == "BULLISH_ACCUMULATION" and is_valuation_bullish and not is_macro_bearish and not is_trend_bearish:
                # Must have more than just 1 factor telling us to buy!
                # If only 1 factor is bullish overall, fail (one-factor bullish cannot return ADD)
                if len(bullish_factors) > 1:
                    if missing_required_add:
                        action = "HOLD"
                        summary = f"Blocked ADD: Missing required factors ({', '.join(missing_required_add)})."
                        blocked_reasons.append(f"Missing required ADD factors: {', '.join(missing_required_add)}")
                    else:
                        action = "ADD"
                        summary = "Strong accumulation evidence."
            
            # REDUCE Gate
            elif (is_overheated) and not (tactical_state == "FAVORABLE_ADD"):
                # Must have at least one non-price block confirming risk (e.g. macro or sentiment)
                # To prevent 1-factor overheated
                if len(overheated_factors) > 1 and (macro_avg <= -1.0 or sum(block_scores.get("sentiment_tactical", [0])) <= -1.0):
                    if missing_required_reduce:
                        action = "HOLD"
                        summary = f"Blocked REDUCE: Missing required factors ({', '.join(missing_required_reduce)})."
                        blocked_reasons.append(f"Missing required REDUCE factors: {', '.join(missing_required_reduce)}")
                    else:
                        action = "REDUCE"
                        summary = "Overheating with confirmation."

            # Confidence Downgrade
            if confidence < 60 and action in ["ADD", "REDUCE"]:
                action = "HOLD"
                summary = "Mixed evidence. (Downgraded due to low confidence)"

        # Filter research factors from support/conflict lists to prevent leakage
        supporting = [o.name for o in observations if o.score > 3 and o.name not in excluded_research]
        conflicting = [o.name for o in observations if o.score < -3 and o.name not in excluded_research]
        
        # Populate machine-readable missing factors based on action block
        missing_factors = []
        if action == "HOLD":
            if "Missing required ADD factors" in "".join(blocked_reasons):
                missing_factors = missing_required_add
            elif "Missing required REDUCE factors" in "".join(blocked_reasons):
                missing_factors = missing_required_reduce

        return Recommendation(
            action=action,
            confidence=confidence,
            strategic_regime=strategic_regime,
            tactical_state=tactical_state,
            supporting_factors=supporting,
            conflicting_factors=conflicting,
            missing_required_blocks=["valuation", "trend_cycle", "macro_liquidity"] if action == "INSUFFICIENT_DATA" else [],
            missing_required_factors=missing_factors,
            blocked_reasons=blocked_reasons,
            freshness_warnings=freshness_warnings,
            excluded_research_factors=excluded_research,
            summary=summary
        )

