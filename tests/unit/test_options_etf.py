import datetime as dt

import pandas as pd

from src.fetchers.binance_fetcher import BinanceFetcher
from src.indicators.options_etf import OptionsETFIndicator

def test_options_wall_support(mocker):
    mock_binance = mocker.Mock(spec=BinanceFetcher)
    indicator = OptionsETFIndicator(binance_fetcher=mock_binance)

    expiry_ts = int(dt.datetime(2026, 3, 27).timestamp() * 1000)
    instruments = [
        {
            "instrument_name": "BTC-27MAR26-20000-P",
            "option_type": "put",
            "strike": 20000,
            "expiration_timestamp": expiry_ts
        },
        {
            "instrument_name": "BTC-27MAR26-19000-P",
            "option_type": "put",
            "strike": 19000,
            "expiration_timestamp": expiry_ts
        }
    ]
    summaries = [
        {
            "instrument_name": "BTC-27MAR26-20000-P",
            "open_interest": 500,
            "underlying_price": 21000
        },
        {
            "instrument_name": "BTC-27MAR26-19000-P",
            "open_interest": 100,
            "underlying_price": 21000
        }
    ]
    mocker.patch.object(indicator, "_fetch_deribit_instruments", return_value=instruments)
    mocker.patch.object(indicator, "_select_target_expiry", return_value=expiry_ts)
    mocker.patch.object(indicator, "_fetch_deribit_book_summary", return_value=summaries)

    result = indicator.get_options_wall_score()
    
    assert result.is_valid is False
    assert result.score == 5.0
    assert "research-only" in result.description.lower()
    assert "support" in result.description.lower()

def test_options_wall_fallback_to_tradier(mocker):
    mock_binance = mocker.Mock(spec=BinanceFetcher)
    indicator = OptionsETFIndicator(binance_fetcher=mock_binance)
    indicator.tradier_token = "token"

    mocker.patch.object(indicator, "_fetch_deribit_instruments", return_value=[])
    mocker.patch.object(indicator, "_fetch_tradier_expirations", return_value=["2030-12-27"])
    mocker.patch.object(indicator, "_select_target_expiry_date", return_value=dt.date(2030, 12, 27))
    mocker.patch.object(
        indicator,
        "_fetch_tradier_chain",
        return_value=[
            {"option_type": "put", "strike": "20", "open_interest": "500"},
            {"option_type": "put", "strike": "18", "open_interest": "100"}
        ]
    )
    mocker.patch.object(indicator, "_fetch_etf_data_cnbc", return_value=(21.0, 1000.0))

    result = indicator.get_options_wall_score()

    assert result.is_valid is False
    assert result.details["source"] == "tradier"
    assert result.score == 5.0
    assert "research-only" in result.description.lower()
    assert "tradier" in result.details["source"]
    assert "put wall" in result.description.lower()

def test_etf_flow_divergence_accumulation(mocker):
    mock_binance = mocker.Mock(spec=BinanceFetcher)
    # Price down from 100 to 95 (< 0.97)
    df_btc = pd.DataFrame({'close': [100, 100, 100, 95]}, index=pd.date_range('2024-01-01', periods=4))
    mock_binance.fetch_ohlcv.return_value = df_btc
    
    indicator = OptionsETFIndicator(binance_fetcher=mock_binance)
    mocker.patch.object(indicator, "_fetch_etf_data_cnbc", return_value=(40.0, 150000.0))

    result = indicator.get_etf_flow_divergence_score()
    
    assert result.is_valid is False
    assert result.score == 5.0
    assert "research-only" in result.description.lower()
    assert "ETF Active" in result.description
