import os
from src.config import Config
from src.state.tracker import StateTracker
from src.indicators.technical import TechnicalIndicator
from src.indicators.macro_liquid import MacroIndicator
from src.indicators.sentiment_cycle import SentimentCycleIndicator
from src.indicators.options_etf import OptionsETFIndicator

class StrategyEngine:
    def __init__(self, tracker=None):
        self.tracker = tracker or StateTracker()
        self.tech = TechnicalIndicator()
        self.macro = MacroIndicator()
        self.sentiment = SentimentCycleIndicator()
        self.opt_etf = OptionsETFIndicator()

    def evaluate(self):
        """
        Run all indicators and aggregate scores.
        """
        results = []
        
        # 1. Technical Indicators
        results.append(self.tech.get_200wma_score())
        results.append(self.tech.get_pi_cycle_score())
        results.append(self.tech.get_rsi_divergence_score())
        
        # 2. Macro Indicators
        results.append(self.macro.get_net_liquidity_score())
        results.append(self.macro.get_yield_divergence_score())
        
        # 3. Sentiment Indicators
        results.append(self.sentiment.get_fear_greed_score())
        results.append(self.sentiment.get_cycle_position_score())
        
        # 4. Options & ETF
        results.append(self.opt_etf.get_options_wall_score())
        results.append(self.opt_etf.get_etf_flow_divergence_score())
        
        return results

    def calculate_final_score(self, results):
        """
        Normalized scoring: (Sum of Score*Weight) / (Sum of Weight) * 10
        Converts sum of points into a 0-100 scale (or -100 to 100).
        """
        valid_weighted_sum = 0.0
        total_weight = 0.0
        
        for res in results:
            # We treat score=0 as potentially missing/neutral, 
            # but here specifically we exclude "Fetch Error" or explicit invalid markers
            if "Insufficient data" in res.description or "Fetch error" in res.description:
                continue
            
            valid_weighted_sum += res.score * res.weight
            total_weight += res.weight
            
        if total_weight == 0:
            return 0.0
            
        # Standardized to -100 to 100 (since individual scores are -10 to 10)
        final_score = (valid_weighted_sum / total_weight) * 10
        return round(final_score, 2)

    def run_strategy_cycle(self, force_buy=False):
        """
        Main execution cycle for a Monday evaluation.
        """
        # Ensure month is up-to-date
        self.tracker.update_for_new_month()
        
        # Run all metrics
        results = self.evaluate()
        final_score = self.calculate_final_score(results)
        
        # Get current price for record
        curr_price = self.tech.fetcher.get_current_price() or 0
        
        decision = "WAIT"
        report_msg = self._generate_report(results, final_score, curr_price)
        
        # Decision Logic
        if final_score >= Config.THRESHOLD_BUY or force_buy:
            if not self.tracker.state["has_bought_this_month"]:
                decision = "BUY"
                multiplier = self.tracker.state["accumulated_budget_multiplier"]
                report_msg += f"\n\n🚨 **DECISION: [BUY]** - Execute DCA with {multiplier}x budget."
                self.tracker.record_action("BUY", final_score, curr_price)
            else:
                decision = "WAIT (Already Bought)"
                report_msg += f"\n\nℹ️ **SIGNAL: [BUY]** - Score meets criteria but DCA already executed this month."
        elif final_score <= Config.THRESHOLD_SELL:
            decision = "ALERT (Take Profit / Rebalance)"
            report_msg += f"\n\n⚠️ **DECISION: [ALERT]** - Portfolio risk high. Consider rebalancing/TP."
            self.tracker.record_action("ALERT", final_score, curr_price)
        else:
            decision = "WAIT"
            report_msg += f"\n\n😴 **DECISION: [WAIT]** - Neutral market conditions."
            # Only record if we want to log every week's score
            self.tracker.record_action("WAIT", final_score, curr_price)

        return decision, report_msg

    def _generate_report(self, results, final_score, price):
        lines = []
        lines.append(f"# BTC Monitor Report - {self.tracker.state['current_month']}")
        lines.append(f"**Final Score:** `{final_score}` / 100")
        lines.append(f"**Price:** ${price:,.2f}")
        lines.append(f"**Budget Multiplier:** {self.tracker.state['accumulated_budget_multiplier']}x")
        lines.append("\n## Multi-Factor Breakdown")
        
        for res in results:
            status_emoji = "✅" if res.score > 0 else "❌" if res.score < 0 else "⚪"
            lines.append(f"- {status_emoji} **{res.name}**: {res.score} (_{res.description}_)")
            
        return "\n".join(lines)

if __name__ == "__main__":
    engine = StrategyEngine()
    dec, msg = engine.run_strategy_cycle()
    print(msg)
