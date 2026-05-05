
import pandas as pd
from src.fetchers.fred_fetcher import FredFetcher
from src.config import Config

fetcher = FredFetcher()
yields = fetcher.get_us10y()
dxy = fetcher.get_dxy()

print("--- YIELDS (DGS10) ---")
if yields is not None:
    print(f"Len: {len(yields)}")
    print(yields.tail(10))
    print(f"Nulls: {yields.isnull().sum()}")
else:
    print("Yields is None")

print("\n--- DXY (DTWEXBGS) ---")
if dxy is not None:
    print(f"Len: {len(dxy)}")
    print(dxy.tail(10))
    print(f"Nulls: {dxy.isnull().sum()}")
else:
    print("DXY is None")
