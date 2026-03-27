import pytest
from src.strategy.incremental_buy_engine import IncrementalBuyEngine
from src.strategy.factor_models import CashAction, FactorObservation
from datetime import datetime

def make_obs(name, score, is_valid=True):
    return FactorObservation(
        name=name,
        score=score,
        is_valid=is_valid,
        details={},
        description="",
        timestamp=datetime.now(),
        freshness_ok=True,
        confidence_penalty=0.0,
        blocked_reason=""
    )

def test_cash_engine_exists():
    """Verify IncrementalBuyEngine can be instantiated."""
    engine = IncrementalBuyEngine()
    assert engine is not None

def test_cash_engine_emits_cash_actions():
    """Verify IncrementalBuyEngine emissions are within CashAction vocabulary."""
    engine = IncrementalBuyEngine()
    obs = [make_obs("MVRV_Proxy", 0.0, is_valid=False)]
    rec = engine.evaluate(obs)
    assert rec.action in [a.value for a in CashAction]

def test_buy_now_on_bullish_regime():
    """Verify BUY_NOW is emitted on favorable strategic and tactical setup."""
    engine = IncrementalBuyEngine()
    obs = [
        make_obs("MVRV_Proxy", 7.0),
        make_obs("Puell_Multiple", 7.0),
        make_obs("200WMA", 7.0),
        make_obs("Cycle_Pos", 7.0),
        make_obs("Net_Liquidity", 7.0),
        make_obs("Yields", 7.0),
        make_obs("RSI_Div", 7.0), # Tactical bullish
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "BUY_NOW"

def test_stagger_buy_on_bullish_regime_with_tactical_veto():
    """Verify STAGGER_BUY is emitted when strategic is bullish but tactical is not."""
    engine = IncrementalBuyEngine()
    obs = [
        make_obs("MVRV_Proxy", 7.0),
        make_obs("Puell_Multiple", 7.0),
        make_obs("200WMA", 7.0),
        make_obs("Cycle_Pos", 7.0),
        make_obs("Net_Liquidity", 7.0),
        make_obs("Yields", 7.0),
        make_obs("FearGreed", -8.0), # Tactical bearish (extreme greed for price action)
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "STAGGER_BUY"

def test_buy_now_requires_required_factor_set():
    """Verify BUY_NOW is downgraded when required buy-now factors are missing/invalid."""
    engine = IncrementalBuyEngine()
    obs = [
        make_obs("MVRV_Proxy", 7.0),
        make_obs("Puell_Multiple", 7.0),
        make_obs("200WMA", 7.0),
        make_obs("Cycle_Pos", 7.0),
        make_obs("Net_Liquidity", 7.0, is_valid=False),  # required_for_buy_now but invalid
        make_obs("Yields", 7.0, is_valid=False),         # required_for_buy_now but invalid
        make_obs("DXY_Regime", 7.0),                     # keeps macro block present -> bullish regime still possible
        make_obs("RSI_Div", 7.0),
    ]
    rec = engine.evaluate(obs)
    assert rec.action == "STAGGER_BUY"
    assert "Yields" in rec.missing_required_factors
    assert "Net_Liquidity" in rec.missing_required_factors
