from typing import List
from src.strategy.factor_models import FactorObservation, Recommendation, CashAction, Layer
from src.strategy.factor_registry import get_factor
from src.strategy.strategic_engine import StrategicEngine, StrategicRegime
from src.strategy.tactical_engine import TacticalEngine
from src.strategy.calibration import CashCalibrator
from src.strategy.block_utils import aggregate_strategic_blocks, compute_agreement_weight


class IncrementalBuyEngine:
    """
    Engine for fresh capital deployment advice (BUY_NOW, STAGGER_BUY, WAIT).
    Focuses on entry timing quality vs benchmarks.
    """
    def __init__(self):
        self.strategic_engine = StrategicEngine()
        self.tactical_engine = TacticalEngine()
        self.calibrator = CashCalibrator()

    def evaluate(self, observations: List[FactorObservation]) -> Recommendation:
        # 1. Infer Strategic Regime
        regime = self.strategic_engine.infer_regime(observations)

        # 2. Evaluate Tactical Evidence
        tactical_info = self.tactical_engine.evaluate_tactical(observations)

        # 3. Decision Logic & Gating
        action = CashAction.WAIT
        confidence = 50
        summary = "Market environment does not favor immediate lump-sum deployment."
        blocked_reasons = []

        if regime == StrategicRegime.INSUFFICIENT_DATA:
            return Recommendation(
                action=CashAction.INSUFFICIENT_DATA.value,
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
                summary="Missing required strategic evidence for buy timing."
            )

        # Aggregate strategic strength via shared utility (C1 fix)
        block_means, _ = aggregate_strategic_blocks(observations)
        agreement_weight = compute_agreement_weight(block_means)

        if regime == StrategicRegime.BULLISH_ACCUMULATION:
            action = CashAction.BUY_NOW
            summary = "Macro and valuation setup favor immediate deployment."

            # Tactical Veto for BUY_NOW — downgrade to STAGGER_BUY
            if tactical_info["tactical_bias"] == "BEARISH_CONFIRMED":
                action = CashAction.STAGGER_BUY
                summary = (
                    "Strategic setup is bullish, but tactical indicators suggest waiting "
                    "for a better intra-week entry. Stagger deployment."
                )
                blocked_reasons.append("Tactical Bearish Veto")

            # Check for specific wait-vetoes in factor registry (C2 fix: specific except)
            if action == CashAction.BUY_NOW:
                for o in observations:
                    if not o.is_valid:
                        continue
                    try:
                        defn = get_factor(o.name)
                    except KeyError:
                        continue
                    if defn.is_wait_veto and o.score < -5.0:
                        action = CashAction.STAGGER_BUY
                        summary = f"Aggressive entry vetoed by {o.name}. Stagger deployment."
                        blocked_reasons.append(f"Veto: {o.name}")
                        break

            # Calibration
            confidence = self.calibrator.calibrate(
                action.value,
                agreement_weight,
                tactical_info["tactical_bias"] == "BULLISH_CONFIRMED"
            )

        elif regime == StrategicRegime.OVERHEATED:
            action = CashAction.WAIT
            summary = "Market is strategically overheated. Wait for a correction."
            confidence = self.calibrator.calibrate(action.value, agreement_weight, False)

        else:  # NEUTRAL
            action = CashAction.WAIT
            summary = "No clear timing advantage detected. Wait or use standard DCA."
            confidence = self.calibrator.calibrate(action.value, agreement_weight, False)

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
            if action == CashAction.BUY_NOW:
                if o.score > 0:
                    supporting.append(o.name)
                elif o.score < 0:
                    conflicting.append(o.name)
            elif action == CashAction.WAIT:
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
            missing_required_factors=[],
            blocked_reasons=blocked_reasons,
            freshness_warnings=warnings,
            excluded_research_factors=research,
            summary=summary
        )
