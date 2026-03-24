import pandas as pd
import os
from src.backtest.base_runner import BaseBacktestRunner
from src.strategy.incremental_buy_engine import IncrementalBuyEngine
from src.backtest.metrics import calculate_forward_returns, evaluate_precision, calculate_benchmark_dca_return

class CashBacktestRunner(BaseBacktestRunner):
    def run(self, output_dir="data/backtest/cash"):
        self.load_data()
        engine = IncrementalBuyEngine()
        records = []
        
        for idx in range(len(self.weekly_df)):
            timestamp = self.weekly_df.index[idx]
            obs = self.get_observations(idx)
            rec = engine.evaluate(obs)
            
            fwd_returns = calculate_forward_returns(self.daily_df["close"], timestamp, [28, 84, 182])
            
            res = {
                "timestamp": timestamp,
                "action": rec.action,
                "regime": rec.strategic_regime,
                "confidence": rec.confidence,
                "price": self.weekly_df["close"].iloc[idx]
            }
            res.update(fwd_returns)
            
            # Precision
            for win in [28, 84, 182]:
                col = f"{win}_day_return"
                if col in fwd_returns:
                    res[f"precision_{win}"] = evaluate_precision(rec.action, fwd_returns[col])
            
            # Benchmark DCA Performance (Relative)
            # Validate both BUY_NOW and STAGGER_BUY against a DCA benchmark:
            # - BUY_NOW succeeds if lump-sum outperforms DCA (rel_dca_perf > 0)
            # - STAGGER_BUY succeeds if DCA outperforms lump-sum (rel_dca_perf < 0)
            if rec.action in ["BUY_NOW", "STAGGER_BUY"]:
                for win in [28, 84]:
                    rel_perf = calculate_benchmark_dca_return(
                        self.daily_df["close"], timestamp, win
                    )
                    res[f"rel_dca_perf_{win}"] = rel_perf
                    if rel_perf is not None:
                        if rec.action == "BUY_NOW":
                            res[f"timing_success_{win}"] = rel_perf > 0
                        else:
                            res[f"timing_success_{win}"] = rel_perf < 0
            
            records.append(res)
            
        df = pd.DataFrame(records)
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, "results.csv"), index=False)
        print(f"Cash backtest results saved to {output_dir}")
        return df

if __name__ == "__main__":
    CashBacktestRunner().run()
