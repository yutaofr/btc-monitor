import argparse
from datetime import datetime
from src.strategy.engine import StrategyEngine
from src.config import Config

def run_evaluation():
    """Trigger a full evaluation cycle and print/notify result."""
    print(f"[{datetime.now().isoformat()}] Starting Market Evaluation Snapshot...")
    engine = StrategyEngine()
    decision, report = engine.run_strategy_cycle()
    
    print("-" * 30)
    print(report)
    print("-" * 30)
    
    print(f"[{datetime.now().isoformat()}] Cycle Complete. Decision: {decision}")

def main():
    parser = argparse.ArgumentParser(description="BTC Monitor DCA & Position Management (Run-Once Tool)")
    parser.add_argument("--now", action="store_true", help="(Deprecated) Kept for backward compatibility. The tool always runs immediately now.")
    args = parser.parse_args()

    # The tool is now a pure CLI utility. Scheduling should be done externally (e.g., via Cron).
    run_evaluation()

if __name__ == "__main__":
    main()

