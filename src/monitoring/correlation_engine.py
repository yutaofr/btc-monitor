import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CorrelationContext:
    correlations: Dict[str, float]
    regime_labels: List[str]
    is_valid: bool = True

class CorrelationEngine:
    """
    TADR Architecture: Contextual Layer
    Computes rolling correlations between BTC and Macro/Equities/Gold.
    
    [MATH DERIVATION: 15% Drift Threshold]
    The 15% Precision Drift Threshold is derived from the standard error of proportion:
    SE = sqrt(p * (1-p) / n). For n=50 (approx 1 year of weekly signals) and p=0.85 (benchmark), 
    SE is approx 5%. A 3*SE move (99.7% confidence) is 15%. 
    Any drop >15% is statistically significant and indicates 'strategy drift'.
    """
    
    def __init__(self, window: int = 90):
        self.window = window
        self.thresholds = {
            "Risk-On": ("SPX", 0.6, "positive"),
            "Safe-Haven": ("Gold", 0.5, "positive"),
            "Liquidity-Driven": ("DXY", -0.5, "negative")
        }

    def classify(self, data: pd.DataFrame) -> CorrelationContext:
        """
        Input: DataFrame with columns ['BTC', 'SPX', 'DXY', 'Gold']
        Calculates Pearson correlation of log returns.
        """
        if len(data) < self.window:
            return CorrelationContext(correlations={}, regime_labels=["Neutral"], is_valid=False)

        # 1. 计算对数收益率 (如果输入不是收益率)
        # 简单判断：如果值大于 1.0 (价格)，则计算收益率
        if (data.abs() > 1.0).any().any():
            returns = data.pct_change().dropna()
        else:
            returns = data

        if len(returns) < self.window - 1:
            return CorrelationContext(correlations={}, regime_labels=["Neutral"], is_valid=False)

        # 2. 计算最近窗口的相关性
        corrs = {}
        target_assets = [col for col in data.columns if col != 'BTC']
        
        last_window = returns.tail(self.window)
        for asset in target_assets:
            if asset in last_window.columns:
                corrs[asset] = last_window['BTC'].corr(last_window[asset])

        # 3. 判定 Regime
        labels = []
        for regime, (asset, threshold, direction) in self.thresholds.items():
            if asset in corrs:
                val = corrs[asset]
                if direction == "positive" and val > threshold:
                    labels.append(regime)
                elif direction == "negative" and val < threshold:
                    labels.append(regime)

        if not labels:
            labels = ["Neutral"]

        return CorrelationContext(correlations=corrs, regime_labels=labels)
