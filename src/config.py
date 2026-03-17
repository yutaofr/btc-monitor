import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
    
    # Notification Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Strategy Thresholds (Scaling 0-100 for final normalized score)
    THRESHOLD_BUY = float(os.getenv("THRESHOLD_BUY", 60.0))
    THRESHOLD_SELL = float(os.getenv("THRESHOLD_SELL", -40.0))
    MAX_BUDGET_MULTIPLIER = float(os.getenv("MAX_BUDGET_MULTIPLIER", 3.0))

    # Timezone
    TIMEZONE = "Europe/Paris"
    
    # Path settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, "data", "state.json")

    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.FRED_API_KEY:
            print("[WARNING] FRED_API_KEY not found. Macro liquidity indicators will be disabled.")
        return True

if __name__ == "__main__":
    # Test loading
    print(f"Threshold Buy: {Config.THRESHOLD_BUY}")
    Config.validate()
