import requests
import pandas as pd
import time

class BlockchainFetcher:
    """
    Fetcher for free, public on-chain data from Blockchain.com and Mempool.space.
    No API keys required.
    """
    def __init__(self):
        self.blockchain_base_url = "https://api.blockchain.info/charts"
        self.mempool_base_url = "https://mempool.space/api"

    def fetch_chart(self, chart_name, timespan="1year"):
        """
        Fetch historical data for a specific chart from Blockchain.info.
        """
        url = f"{self.blockchain_base_url}/{chart_name}"
        params = {
            "timespan": timespan,
            "format": "json",
            "sampled": "false" # Get all points for better MA calculation
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            if "values" not in data:
                return None
            
            df = pd.DataFrame(data["values"])
            df['timestamp'] = pd.to_datetime(df['x'], unit='s')
            df.set_index('timestamp', inplace=True)
            df.rename(columns={'y': 'value'}, inplace=True)
            return df
        except Exception as e:
            print(f"[ERROR] Blockchain.info fetch failed for {chart_name}: {e}")
            return None

    def get_miners_revenue(self, timespan="1year"):
        return self.fetch_chart("miners-revenue", timespan)

    def get_hash_rate(self, timespan="1year"):
        return self.fetch_chart("hash-rate", timespan)

    def get_difficulty(self):
        """
        Fetch current network difficulty from Mempool.space.
        """
        try:
            resp = requests.get(f"{self.mempool_base_url}/v1/difficulty-adjustment", timeout=10)
            return resp.json()
        except Exception as e:
            print(f"[ERROR] Mempool.space difficulty fetch failed: {e}")
            return None

    def get_current_stats(self):
        """
        Fetch latest network stats from Blockchain.info.
        """
        try:
            resp = requests.get("https://api.blockchain.info/stats", timeout=10)
            return resp.json()
        except Exception as e:
            print(f"[ERROR] Blockchain.info stats fetch failed: {e}")
            return None

if __name__ == "__main__":
    fetcher = BlockchainFetcher()
    print("Testing Miners Revenue...")
    df = fetcher.get_miners_revenue(timespan="5days")
    if df is not None:
        print(df.tail())
    
    print("\nTesting Difficulty...")
    diff = fetcher.get_difficulty()
    print(diff)
