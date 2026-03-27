import os

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    # API Keys
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
    TRADIER_API_TOKEN = os.getenv("TRADIER_API_TOKEN")
    
    # Notification Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Legacy Execution Thresholds (Deprecated by Stateless Advisory Engine)
    THRESHOLD_BUY = float(os.getenv("THRESHOLD_BUY", 60.0))
    THRESHOLD_SELL = float(os.getenv("THRESHOLD_SELL", -40.0))
    MAX_BUDGET_MULTIPLIER = float(os.getenv("MAX_BUDGET_MULTIPLIER", 3.0))

    # Timezone
    TIMEZONE = "UTC" # 指令 [3.3.3]: 强制 UTC
    
    # TADR 核心算法参数 [指令 2.2]
    TADR_REDUNDANCY_THETA = 0.8
    TADR_REDUNDANCY_K = 15
    TADR_REDUNDANCY_MAX_PENALTY = 0.4
    
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
