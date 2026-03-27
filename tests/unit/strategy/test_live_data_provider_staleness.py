import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.strategy.live_data_provider import LiveDataProvider

def test_live_data_provider_staleness_interception():
    """
    指令 [2.1] 验证：如果宏观数据最后更新时间超过 72 小时，必须返回 None。
    """
    mock_binance = MagicMock()
    mock_fred = MagicMock()
    
    # 1. BTC 数据直到今天 (2026-03-27)
    btc_dates = pd.date_range(end="2026-03-27", periods=10)
    mock_binance.fetch_ohlcv.return_value = pd.DataFrame({'close': [60000]*10}, index=btc_dates)
    
    # 2. 宏观数据严重过期 (最后更新在 4 天前，即 2026-03-23)
    stale_dates = pd.date_range(end="2026-03-23", periods=10)
    mock_fred.get_series.side_effect = [
        pd.Series([100.0]*10, index=stale_dates), # DXY
        pd.Series([5000.0]*10, index=stale_dates) # SPX
    ]
    
    # 默认 72 小时阈值
    provider = LiveDataProvider(binance=mock_binance, fred=mock_fred, max_staleness_hours=72)
    df = provider.get_sync_market_data(window=5)
    
    # 预期因数据过期（2026-03-27 vs 2026-03-23 = 96h > 72h）而返回 None
    assert df is None

def test_live_data_provider_acceptable_staleness():
    """验证在允许范围内的延迟（如周末）应通过。"""
    mock_binance = MagicMock()
    mock_fred = MagicMock()
    
    # BTC 是周一 (2026-03-30)
    btc_dates = pd.date_range(end="2026-03-30", periods=5)
    mock_binance.fetch_ohlcv.return_value = pd.DataFrame({'close': [60000]*5}, index=btc_dates)
    
    # 宏观数据最后更新是上周五 (2026-03-27)，延迟约 72 小时
    macro_dates = pd.date_range(end="2026-03-27", periods=5)
    mock_fred.get_series.side_effect = [
        pd.Series([100.0]*5, index=macro_dates),
        pd.Series([5000.0]*5, index=macro_dates)
    ]
    
    provider = LiveDataProvider(binance=mock_binance, fred=mock_fred, max_staleness_hours=73) # 允许周末 72h + 1h 缓存
    df = provider.get_sync_market_data(window=3)
    
    # 预期通过
    assert df is not None
    assert "BTC" in df.columns
