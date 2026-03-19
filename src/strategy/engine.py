from src.config import Config
from src.indicators.macro_liquid import MacroIndicator
from src.indicators.options_etf import OptionsETFIndicator
from src.indicators.sentiment_cycle import SentimentCycleIndicator
from src.indicators.technical import TechnicalIndicator
from src.indicators.valuation import ValuationIndicator
from src.state.tracker import StateTracker
from src.strategy.policies import (
    COMBINED_LAYER_WEIGHTS,
    RESEARCH_FACTORS,
    classify_factor,
)
from src.strategy.execution_engine import ExecutionEngine
from src.strategy.strategic_engine import StrategicEngine
from src.strategy.tactical_engine import TacticalEngine
from src.strategy.reporting import build_report


class StrategyEngine:
    def __init__(self, tracker=None):
        self.tracker = tracker or StateTracker()
        self.tech = TechnicalIndicator()
        self.macro = MacroIndicator()
        self.sentiment = SentimentCycleIndicator()
        self.opt_etf = OptionsETFIndicator()
        self.valuation = ValuationIndicator()
        self.strategic_engine = StrategicEngine()
        self.tactical_engine = TacticalEngine()
        self.execution_engine = ExecutionEngine()

    def _is_research_only(self, result):
        if result.details.get("research_only"):
            return True
        description = (result.description or "").strip().lower()
        return description.startswith("research-only") or result.name in RESEARCH_FACTORS

    def split_results(self, results):
        buckets = {"strategic": [], "tactical": [], "research": [], "unknown": []}

        for result in results:
            bucket = classify_factor(result.name, research_only=self._is_research_only(result))
            buckets.setdefault(bucket, []).append(result)

        return buckets

    def _has_valid_results(self, results):
        return any(result.is_valid and not self._is_research_only(result) for result in results)

    def evaluate(self):
        """
        Run all indicators and aggregate scores.
        """
        results = []

        results.append(self.tech.get_200wma_score())
        results.append(self.tech.get_pi_cycle_score())
        results.append(self.tech.get_rsi_divergence_score())

        results.append(self.macro.get_net_liquidity_score())
        results.append(self.macro.get_yield_divergence_score())

        results.append(self.sentiment.get_fear_greed_score())
        results.append(self.sentiment.get_cycle_position_score())

        res_mvrv = self.valuation.get_mvrv_proxy_score()
        res_mvrv.weight = 1.5
        results.append(res_mvrv)

        res_puell = self.valuation.get_puell_multiple_score()
        res_puell.weight = 1.2
        results.append(res_puell)

        res_prod = self.valuation.get_production_cost_score()
        res_prod.weight = 1.0
        results.append(res_prod)

        results.append(self.opt_etf.get_options_wall_score())
        results.append(self.opt_etf.get_etf_flow_divergence_score())

        return results

    def calculate_final_score(self, results):
        split_results = self.split_results(results)
        strategic_score = self.strategic_engine.calculate_score(split_results["strategic"])
        tactical_score = self.tactical_engine.calculate_score(split_results["tactical"])
        has_strategic = self._has_valid_results(split_results["strategic"])
        has_tactical = self._has_valid_results(split_results["tactical"])

        if not has_strategic:
            return 0.0

        total_weight = COMBINED_LAYER_WEIGHTS["strategic"]
        final_score = strategic_score * COMBINED_LAYER_WEIGHTS["strategic"]

        if has_tactical:
            total_weight += COMBINED_LAYER_WEIGHTS["tactical"]
            final_score += tactical_score * COMBINED_LAYER_WEIGHTS["tactical"]

        final_score = final_score / total_weight
        return round(final_score, 2)

    def run_strategy_cycle(self, force_buy=False):
        """
        Main execution cycle for a market evaluation.
        """
        self.tracker.update_for_new_month()

        results = self.evaluate()
        split_results = self.split_results(results)
        strategic_score = self.strategic_engine.calculate_score(split_results["strategic"])
        tactical_score = self.tactical_engine.calculate_score(split_results["tactical"])
        final_score = self.calculate_final_score(results)
        execution = self.execution_engine.decide(
            strategic_score,
            tactical_score,
            self.tracker.state.get("accumulated_budget_multiplier", 1.0),
            monthly_action_count=self.tracker.state.get("monthly_action_count", 0),
            force_buy=force_buy,
        )

        curr_price = self.tech.fetcher.get_current_price() or 0

        decision = execution.action
        report_msg = self._generate_report(
            results,
            final_score,
            curr_price,
            strategic_score=strategic_score,
            tactical_score=tactical_score,
            regime=execution.regime,
            timing=execution.timing,
        )

        if execution.action == "BUY":
            report_msg += f"\n\n🚨 **DECISION: [BUY]** - Execute DCA with {execution.budget_multiplier}x budget."
            self.tracker.record_action(
                "BUY",
                final_score,
                curr_price,
                budget_multiplier_used=execution.budget_multiplier,
                metadata={"regime": execution.regime, "timing": execution.timing},
            )
        elif execution.action == "PARTIAL_BUY":
            report_msg += f"\n\n🪜 **DECISION: [PARTIAL_BUY]** - Execute staggered DCA with {execution.budget_multiplier}x budget."
            self.tracker.record_action(
                "PARTIAL_BUY",
                final_score,
                curr_price,
                budget_multiplier_used=execution.budget_multiplier,
                metadata={"regime": execution.regime, "timing": execution.timing},
            )
        elif execution.action == "ALERT":
            report_msg += "\n\n⚠️ **DECISION: [ALERT]** - Portfolio risk high. Consider rebalancing/TP."
            self.tracker.record_action(
                "ALERT",
                final_score,
                curr_price,
                budget_multiplier_used=0.0,
                metadata={"regime": execution.regime, "timing": execution.timing},
            )
        elif execution.action == "WAIT (Already Acted)":
            report_msg += "\n\nℹ️ **SIGNAL: [WAIT]** - Buy setup exists but an action already executed this month."
        else:
            report_msg += "\n\n😴 **DECISION: [WAIT]** - Neutral market conditions."
            self.tracker.record_action(
                "WAIT",
                final_score,
                curr_price,
                budget_multiplier_used=0.0,
                metadata={"regime": execution.regime, "timing": execution.timing},
            )

        return decision, report_msg

    def _generate_report(self, results, final_score, price, strategic_score=None, tactical_score=None, regime=None, timing=None):
        split_results = self.split_results(results)
        strategic_score = strategic_score if strategic_score is not None else self.strategic_engine.calculate_score(split_results["strategic"])
        tactical_score = tactical_score if tactical_score is not None else self.tactical_engine.calculate_score(split_results["tactical"])
        return build_report(
            results=results,
            final_score=final_score,
            price=price,
            budget_multiplier=self.tracker.state["accumulated_budget_multiplier"],
            strategic_score=strategic_score,
            tactical_score=tactical_score,
            regime=regime or "UNSPECIFIED",
            timing=timing or "UNSPECIFIED",
            is_research_only=self._is_research_only,
        )


if __name__ == "__main__":
    engine = StrategyEngine()
    dec, msg = engine.run_strategy_cycle()
    print(msg)
