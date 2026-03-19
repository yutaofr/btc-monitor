from dataclasses import dataclass


@dataclass
class ExecutionDecision:
    regime: str
    timing: str
    action: str
    budget_multiplier: float
    reason: str


class ExecutionEngine:
    def classify_regime(self, strategic_score):
        if strategic_score >= 70.0:
            return "AGGRESSIVE_ACCUMULATE"
        if strategic_score >= 50.0:
            return "NORMAL_ACCUMULATE"
        if strategic_score >= 30.0:
            return "DEFENSIVE_HOLD"
        return "RISK_REDUCE"

    def classify_timing(self, tactical_score):
        if tactical_score >= 65.0:
            return "BUY_NOW"
        if tactical_score >= 45.0:
            return "STAGGER_BUY"
        return "WAIT"

    def decide(
        self,
        strategic_score,
        tactical_score,
        available_budget_multiplier,
        monthly_action_count=0,
        force_buy=False,
    ):
        available_budget_multiplier = max(0.0, float(available_budget_multiplier or 0.0))

        if force_buy:
            budget = round(max(1.0, available_budget_multiplier), 2)
            return ExecutionDecision(
                regime="FORCED",
                timing="BUY_NOW",
                action="BUY",
                budget_multiplier=budget,
                reason="Force-buy override",
            )

        regime = self.classify_regime(strategic_score)
        timing = self.classify_timing(tactical_score)

        if monthly_action_count >= 1 and timing != "WAIT":
            return ExecutionDecision(
                regime=regime,
                timing=timing,
                action="WAIT (Already Acted)",
                budget_multiplier=0.0,
                reason="Monthly action already executed",
            )

        if regime == "RISK_REDUCE":
            return ExecutionDecision(
                regime=regime,
                timing="WAIT",
                action="ALERT",
                budget_multiplier=0.0,
                reason="Structural risk regime",
            )

        if regime == "DEFENSIVE_HOLD":
            return ExecutionDecision(
                regime=regime,
                timing=timing,
                action="WAIT",
                budget_multiplier=0.0,
                reason="Defensive hold regime",
            )

        if regime == "AGGRESSIVE_ACCUMULATE":
            if timing == "BUY_NOW":
                budget = round(max(1.0, available_budget_multiplier), 2)
                return ExecutionDecision(
                    regime=regime,
                    timing=timing,
                    action="BUY",
                    budget_multiplier=budget,
                    reason="Aggressive accumulate regime with strong timing",
                )
            if timing == "STAGGER_BUY":
                budget = min(available_budget_multiplier, max(1.0, round(available_budget_multiplier / 2.0, 2)))
                return ExecutionDecision(
                    regime=regime,
                    timing=timing,
                    action="PARTIAL_BUY",
                    budget_multiplier=round(budget, 2),
                    reason="Aggressive regime with partial timing confirmation",
                )

        if regime == "NORMAL_ACCUMULATE":
            if timing == "BUY_NOW":
                return ExecutionDecision(
                    regime=regime,
                    timing=timing,
                    action="BUY",
                    budget_multiplier=round(min(available_budget_multiplier, 1.0), 2),
                    reason="Normal accumulate regime with strong timing",
                )
            if timing == "STAGGER_BUY":
                return ExecutionDecision(
                    regime=regime,
                    timing=timing,
                    action="PARTIAL_BUY",
                    budget_multiplier=round(min(available_budget_multiplier, 0.5), 2),
                    reason="Normal accumulate regime with partial timing confirmation",
                )

        return ExecutionDecision(
            regime=regime,
            timing=timing,
            action="WAIT",
            budget_multiplier=0.0,
            reason="Timing confirmation not strong enough",
        )
