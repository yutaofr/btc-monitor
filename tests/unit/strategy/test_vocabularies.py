import pytest
from src.strategy.factor_models import PositionAction, CashAction

def test_position_actions():
    """Verify PositionAction has correct members."""
    expected = {"ADD", "REDUCE", "HOLD", "INSUFFICIENT_DATA"}
    members = {a.name for a in PositionAction}
    assert members == expected

def test_cash_actions():
    """Verify CashAction has correct members."""
    expected = {"BUY_NOW", "STAGGER_BUY", "WAIT", "INSUFFICIENT_DATA"}
    members = {a.name for a in CashAction}
    assert members == expected

def test_no_overlap_except_insufficient_data():
    """Verify no accidental overlap between branches except INSUFFICIENT_DATA."""
    pos_members = {a.name for a in PositionAction if a.name != "INSUFFICIENT_DATA"}
    cash_members = {a.name for a in CashAction if a.name != "INSUFFICIENT_DATA"}
    
    overlap = pos_members.intersection(cash_members)
    assert not overlap, f"Branches overlap on labels: {overlap}"
