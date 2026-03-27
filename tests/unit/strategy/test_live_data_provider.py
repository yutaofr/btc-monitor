import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.strategy.live_data_provider import LiveDataProvider

def test_live_data_provider_alignment():
    """
    验证 LiveDataProvider 是否能同步对齐不同频次的资产数据。
    - BTC (Daily)
    - SPX (Daily, Tradable days)
    - DXY (Daily, Tradable days)
    """
    # 模拟 Fetchers 输出
    mock_binance = MagicMock()
    mock_fred = MagicMock()
    
    # 构造 BTC 数据 (100天)
    dates = pd.date_range(end="2026-03-27", periods=100)
    mock_binance.fetch_ohlcv.return_value = pd.DataFrame({'close': [60000 + i*10 for i in range(100)]}, index=dates)
    
    # 构造宏观数据 (只有工作日)
    macro_dates = pd.bdate_range(end="2026-03-27", periods=100)
    mock_fred.get_series.side_effect = [
        pd.Series([100 + i*0.1 for i in range(100)], index=macro_dates), # DXY
        pd.Series([5000 + i for i in range(100)], index=macro_dates)     # SPX
    ]
    
    provider = LiveDataProvider(binance=mock_binance, fred=mock_fred)
    df = provider.get_sync_market_data(window=90)
    
    # 1. 验证列名
    assert set(df.columns) == {"BTC", "SPX", "DXY"}
    
    # 2. 验证长度 (应至少为 90 天)
    assert len(df) >= 90
    
    # 3. 验证无空值 (已执行对齐填充)
    assert not df.isnull().values.any()
    
    # 4. 验证最近日期一致
    assert df.index[-1] == pd.Timestamp("2026-03-27")

def test_provider_insufficient_data():
    """验证数据不足时的处理。"""
    mock_binance = MagicMock()
    mock_binance.fetch_ohlcv.return_value = pd.DataFrame({'close': [1.0]}, index=[pd.Timestamp("2026-03-27")])
    
    provider = LiveDataProvider(binance=mock_binance, fred=MagicMock())
    df = provider.get_sync_market_data(window=90)
    
    assert df is None
