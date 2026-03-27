from typing import List, Set, Dict
from datetime import datetime
from src.strategy.factor_models import FactorObservation, Recommendation, PositionAction, Layer
from src.strategy.factor_registry import get_factor, get_all_factors
from src.strategy.strategic_engine import StrategicEngine, StrategicRegime
from src.strategy.tactical_engine import TacticalEngine
from src.strategy.calibration import PositionCalibrator
from src.strategy.block_utils import aggregate_strategic_blocks, compute_agreement_weight


class PositionAdvisoryEngine:
    """
    Refactored engine for position-adjustment advice (ADD, REDUCE, HOLD).
    """
    def __init__(self):
        self.strategic_engine = StrategicEngine()
        self.tactical_engine = TacticalEngine()
        self.calibrator = PositionCalibrator()

    def evaluate(self, observations: List[FactorObservation]) -> Recommendation:
        # 1. Infer Strategic Regime
        regime = self.strategic_engine.infer_regime(observations)

        # 2. Evaluate Tactical Evidence
        tactical_info = self.tactical_engine.evaluate_tactical(observations)

        # 3. Decision Logic & Gating
        action = PositionAction.HOLD
        confidence = 50
        summary = "Market is in a neutral or transitional phase."
        blocked_reasons = []
        
        # Collect all required factors from registry for RCA
        all_factors = get_all_factors()
        valid_factor_names = {o.name for o in observations if o.is_valid}
        
        if regime == StrategicRegime.INSUFFICIENT_DATA:
            return Recommendation(
                action=PositionAction.INSUFFICIENT_DATA.value,
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

        # Aggregate strategic strength via shared utility (C1 fix)
        block_means, strategic_factor_count = aggregate_strategic_blocks(observations)
        agreement_weight = compute_agreement_weight(block_means)

        if regime == StrategicRegime.BULLISH_ACCUMULATION:
            action = PositionAction.ADD
            summary = "High-confidence bullish accumulation regime confirmed."

            # [GATING LOGIC for ADD]
            required_add_factors = [f for f in all_factors if f.is_required_for_add]
            missing_required_factors = sorted([f.name for f in required_add_factors if f.name not in valid_factor_names])
            
            # FAIL-CLOSED: Block if any CRITICAL factor is missing
            critical_missing = [f.name for f in required_add_factors if f.is_critical and f.name not in valid_factor_names]
            
            # FAIL-CLOSED: Block if any BLOCK is entirely missing
            covered_strategic_blocks = {get_factor(o.name).block for o in observations if o.is_valid and get_factor(o.name).layer == Layer.STRATEGIC.value}
            required_blocks = {"valuation", "trend_cycle", "macro_liquidity"}
            missing_blocks = sorted(list(required_blocks - covered_strategic_blocks))

            if critical_missing:
                action = PositionAction.HOLD
                confidence = 50
                summary = f"Required ADD evidence is incomplete: missing {', '.join(critical_missing)}."
                blocked_reasons.append("Required critical factors missing")
            elif missing_blocks:
                action = PositionAction.HOLD
                confidence = 50
                summary = f"Required ADD evidence is incomplete (missing block: {', '.join(missing_blocks)})."
                blocked_reasons.append("Required ADD block coverage missing")

            # Check evidence overload
            is_evidence_overload = False
            try:
                val_obs = [o for o in observations if o.is_valid and get_factor(o.name).block == "valuation"]
                trd_obs = [o for o in observations if o.is_valid and get_factor(o.name).block == "trend_cycle"]
                mac_obs = [o for o in observations if o.is_valid and get_factor(o.name).block == "macro_liquidity"]
                valuation_score = sum(o.score * get_factor(o.name).default_weight for o in val_obs)
                trend_score = sum(o.score * get_factor(o.name).default_weight for o in trd_obs)
                macro_score = sum(o.score * get_factor(o.name).default_weight for o in mac_obs)
                if valuation_score > 12.0 and trend_score > 5.0 and macro_score <= 0.0:
                    is_evidence_overload = True
            except (KeyError, TypeError, ZeroDivisionError):
                pass

            if tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                action = PositionAction.HOLD
                confidence = 50
                summary = "Tactical setup is bearishly overstretched; holding despite bullish regime."
                blocked_reasons.append("Tactical Bearish Conflict")
            else:
                # Gating: Selective but reachable
                if action == PositionAction.ADD and not is_evidence_overload:
                    has_strong_strategic_proof = (
                        strategic_factor_count >= 5 and
                        len(block_means) >= 3 and
                        all(avg > 3.0 for avg in block_means)
                    )
                    if tactical_info["tactical_bias"] == "NEUTRAL" and has_strong_strategic_proof:
                        pass
                    elif tactical_info["tactical_bias"] != "BULLISH_CONFIRMED":
                        action = PositionAction.HOLD
                        summary = "Tactical confirmation required for ADD."
                        blocked_reasons.append("Tactical Confirmation Missing")
                    elif agreement_weight < 5.5:
                        action = PositionAction.HOLD
                        summary = "Strategic strength is insufficient for high-confidence ADD."
                        blocked_reasons.append(f"Low Agreement ({agreement_weight:.1f})")

                # Calibration — single authoritative source (C3 fix: no post-mutation)
                confidence = self.calibrator.calibrate(
                    regime.value,
                    agreement_weight,
                    tactical_info["tactical_bias"] == "BULLISH_CONFIRMED"
                )

        elif regime == StrategicRegime.OVERHEATED:
            action = PositionAction.REDUCE
            summary = "Market showing signs of cyclical overheating."

            required_reduce_factors = [f for f in all_factors if f.is_required_for_reduce]
            missing_required_factors = sorted([f.name for f in required_reduce_factors if f.name not in valid_factor_names])
            
            # [BLOCK GATING LOGIC for REDUCE]
            # REDUCE requires trend_cycle + (valuation OR macro_liquidity)
            covered_strategic_blocks = {get_factor(o.name).block for o in observations if o.is_valid and get_factor(o.name).layer == Layer.STRATEGIC.value}
            has_trend = "trend_cycle" in covered_strategic_blocks
            has_other = "valuation" in covered_strategic_blocks or "macro_liquidity" in covered_strategic_blocks

            if not has_trend or not has_other:
                action = PositionAction.HOLD
                confidence = 50
                summary = "Required REDUCE evidence is incomplete (needs Trend + 1 other block coverage)."
                blocked_reasons.append("Required REDUCE block coverage missing")

            if action == PositionAction.REDUCE and agreement_weight < 4.5:
                action = PositionAction.HOLD
                summary = "Strategic strength is insufficient for high-confidence REDUCE."
                blocked_reasons.append(f"Low Agreement ({agreement_weight:.1f})")

            # Cyclic Breakdown Confirmation (EMA21)
            if action == PositionAction.REDUCE:
                ema21_obs = next((o for o in observations if o.name == "EMA21_Weekly"), None)
                if ema21_obs and ema21_obs.is_valid:
                    rel_dist = ema21_obs.details.get("rel_dist", 1.0)
                    if rel_dist > 0.0:
                        action = PositionAction.HOLD
                        summary = "Strategic overheating detected, but price has not definitively broken 21w EMA support."
                        blocked_reasons.append(f"EMA21 Support Holding ({rel_dist:+.1%})")

            # Tactical Requirement: Must not be strongly bullish
            if action == PositionAction.REDUCE and tactical_info["tactical_bias"] == "BULLISH_CONFIRMED":
                action = PositionAction.HOLD
                summary = "Tactical momentum is still strongly bullish; holding despite overheating signs."
                blocked_reasons.append("Tactical Bullish Conflict")

            # Calibration — single authoritative source (C3 fix: no post-mutation)
            confidence = self.calibrator.calibrate(
                regime.value,
                agreement_weight,
                tactical_info["tactical_bias"] == "BEARISH_CONFIRMED"
            )
        
        else: # NEUTRAL
            missing_required_factors = []

        confidence = max(0, min(100, confidence))  # clamp

        # Check deep value for macro exception
        is_deep_value = False
        sma200_obs = next((o for o in observations if o.name == "SMA200_Weekly"), None)
        if sma200_obs and sma200_obs.is_valid:
            if sma200_obs.details.get("rel_dist", 0.0) < -0.30:
                is_deep_value = True

        # ABSOLUTE NO-CONFLICT GATE
        for o in observations:
            if not o.is_valid:
                continue
            try:
                defn = get_factor(o.name)
            except KeyError:
                continue
            if defn.layer == Layer.RESEARCH.value:
                continue

            if action == PositionAction.ADD and o.score < -5.0:
                if o.name == "EMA21_Weekly":
                    continue
                if defn.block == "macro_liquidity" and is_deep_value:
                    continue
                action = PositionAction.HOLD
                confidence = 50
                summary = f"Action ADD blocked by significant conflicting evidence: {o.name} ({o.score})"
                blocked_reasons.append(f"Veto: {o.name}")
                break
            if action == PositionAction.REDUCE and o.score > 5.0:
                if defn.block in ["trend_cycle", "macro_liquidity"]:
                    continue
                if defn.layer == Layer.TACTICAL.value:
                    continue
                action = PositionAction.HOLD
                confidence = 50
                summary = f"Action REDUCE blocked by significant conflicting evidence: {o.name} ({o.score})"
                blocked_reasons.append(f"Veto: {o.name}")
                break

        # Supporting / Conflicting / Research Lists
        supporting: List[str] = []
        conflicting: List[str] = []
        research: List[str] = []

        for o in observations:
            try:
                defn = get_factor(o.name)
            except KeyError:
                continue
            if defn.layer == Layer.RESEARCH.value:
                research.append(o.name)
                continue
            if not o.is_valid:
                continue
            if action == PositionAction.ADD:
                if o.score > 0:
                    supporting.append(o.name)
                elif o.score < 0:
                    conflicting.append(o.name)
            elif action == PositionAction.REDUCE:
                if o.score < 0:
                    supporting.append(o.name)
                elif o.score > 0:
                    conflicting.append(o.name)

        warnings = [f"{o.name} is stale" for o in observations if not o.freshness_ok]

        return Recommendation(
            action=action.value,
            confidence=min(100, max(0, confidence)),
            strategic_regime=regime.value,
            tactical_state=tactical_info["tactical_bias"],
            supporting_factors=supporting[:5],
            conflicting_factors=conflicting[:5],
            missing_required_blocks=[],
            missing_required_factors=missing_required_factors,
            blocked_reasons=blocked_reasons,
            freshness_warnings=warnings,
            excluded_research_factors=research,
            summary=summary
        )
