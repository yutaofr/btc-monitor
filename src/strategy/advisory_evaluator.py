from src.indicators.macro_liquid import MacroIndicator
from src.indicators.options_etf import OptionsETFIndicator
from src.indicators.sentiment_cycle import SentimentCycleIndicator
from src.indicators.technical import TechnicalIndicator
from src.indicators.valuation import ValuationIndicator

class AdvisoryEvaluator:
    """
    Stateless evaluator that runs all indicator fetchers and aggregates
    the resulting IndicatorResults without coupling to execution logic.
    """
    def __init__(self):
        self.tech = TechnicalIndicator()
        self.macro = MacroIndicator()
        self.sentiment = SentimentCycleIndicator()
        self.opt_etf = OptionsETFIndicator()
        self.valuation = ValuationIndicator()
        
    def evaluate_all(self):
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

    def get_current_price(self):
        return self.tech.fetcher.get_current_price()
