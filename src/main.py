import argparse
import time
import schedule
import pytz
from datetime import datetime
from src.strategy.engine import StrategyEngine
from src.config import Config

def run_evaluation():
    """Trigger a full evaluation cycle and print/notify result."""
    print(f"[{datetime.now().isoformat()}] Starting Weekly Evaluation...")
    engine = StrategyEngine()
    decision, report = engine.run_strategy_cycle()
    
    print("-" * 30)
    print(report)
    print("-" * 30)
    
    # Placeholder for actual notification service call
    # if Config.TELEGRAM_BOT_TOKEN:
    #     send_telegram(report)
    
    print(f"[{datetime.now().isoformat()}] Cycle Complete. Decision: {decision}")

def main():
    parser = argparse.ArgumentParser(description="BTC Monitor DCA & Position Management")
    parser.add_argument("--now", action="store_true", help="Run evaluation snapshot immediately and exit")
    args = parser.parse_args()

    if args.now:
        run_evaluation()
        return

    # Scheduling: Every Monday at 21:00 Paris Time
    paris_tz = pytz.timezone(Config.TIMEZONE)
    print(f"Starting Scheduler... Target: Every Monday 21:00 ({Config.TIMEZONE})")
    
    # schedule library uses local time by default if not specified. 
    # For simplicity in Docker (where TZ=Europe/Paris is set), we use simple 21:00.
    schedule.every().monday.at("21:00").do(run_evaluation)

    # Initial check
    print("Scheduler active. Waiting for next trigger...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
