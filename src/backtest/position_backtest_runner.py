import pandas as pd
import os
from src.backtest.base_runner import BaseBacktestRunner
from src.strategy.position_advisory_engine import PositionAdvisoryEngine
from src.backtest.metrics import calculate_forward_returns, evaluate_precision

class PositionBacktestRunner(BaseBacktestRunner):
    def run(self, output_dir="data/backtest/position"):
        self.load_data()
        engine = PositionAdvisoryEngine()
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
            
            records.append(res)
            
        df = pd.DataFrame(records)
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, "results.csv"), index=False)
        print(f"Position backtest results saved to {output_dir}")
        return df

if __name__ == "__main__":
    PositionBacktestRunner().run()
