"""
Base class for backtest runners, providing shared data loading and factor scoring substrate.
"""
import pandas as pd
import numpy as np
from typing import List
from src.strategy.factor_models import FactorObservation
from src.strategy.factor_registry import get_factor
from src.backtest.advisory_history import (
    IndicatorResult, _to_weekly_ohlcv, calculate_rsi,
    _load_macro_series, _prepare_valuation_series, _load_btc_daily,
    _score_technical, _score_macro, _score_valuation,
    _prepare_fng_series
)


class BaseBacktestRunner:
    def __init__(self):
        self.daily_df = None
        self.weekly_df = None
        self.rsi_weekly = None
        self.net_liq = None
        self.yields = None
        self.dxy = None
        self.mvrv = None
        self.puell = None
        self.hash = None
        self.fng = None

    def load_data(self):
        self.daily_df, _ = _load_btc_daily()
        if self.daily_df is None or self.daily_df.empty:
            raise ValueError("No BTC data available")

        self.weekly_df = _to_weekly_ohlcv(self.daily_df)
        self.rsi_weekly = calculate_rsi(self.weekly_df["close"], period=14)
        self.net_liq, self.yields, self.dxy = _load_macro_series(self.weekly_df.index)
        self.mvrv, self.puell, self.hash = _prepare_valuation_series(self.weekly_df.index)
        self.fng = _prepare_fng_series(self.weekly_df.index)

    def get_observations(self, idx: int) -> List[FactorObservation]:
        timestamp = self.weekly_df.index[idx]
        results = _score_technical(self.weekly_df, self.rsi_weekly, idx)
        results.extend(_score_macro(self.net_liq, self.yields, self.dxy, idx))
        results.extend(_score_valuation(self.mvrv, self.puell, self.hash, self.weekly_df, idx))

        # M1 fix: always append FearGreed — invalid when data is missing, so gating is consistent
        fng_val = self.fng.iloc[idx] if self.fng is not None and idx < len(self.fng) else np.nan
        if pd.isna(fng_val):
            results.append(IndicatorResult("FearGreed", 0.0, is_valid=False,
                                           details={"reason": "Data unavailable"}))
        else:
            fng_score = (50 - fng_val) / 5.0
            results.append(IndicatorResult("FearGreed", round(fng_score, 2), details={"value": fng_val}))

        ath_so_far = self.weekly_df["high"].iloc[:idx + 1].max()
        curr_p = self.weekly_df["close"].iloc[idx]
        drawdown = (curr_p - ath_so_far) / ath_so_far
        if drawdown < -0.7:
            cp_score = 10.0
        elif drawdown > -0.1:
            cp_score = -10.0
        else:
            cp_score = ((-drawdown - 0.4) / 0.3) * 10
        results.append(IndicatorResult("Cycle_Pos", round(cp_score, 2), details={"drawdown": drawdown}))

        observations = []
        for res in results:
            try:
                get_factor(res.name)  # validate factor exists in registry
            except KeyError:
                continue
            observations.append(FactorObservation(
                name=res.name,
                score=res.score,
                is_valid=res.is_valid,
                details=res.details or {},
                description="",
                timestamp=timestamp,
                freshness_ok=True,
                confidence_penalty=0.0 if res.is_valid else 10.0,
                blocked_reason=""
            ))
        return observations
