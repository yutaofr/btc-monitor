import json
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from src.state.tracker import StateTracker

@pytest.fixture
def temp_state_file(tmp_path):
    return tmp_path / "test_state.json"


def _paris_time(year, month, day):
    return datetime(year, month, day, 12, 0, tzinfo=ZoneInfo("Europe/Paris"))

def test_state_init_new_file(temp_state_file):
    tracker = StateTracker(data_path=str(temp_state_file), now_fn=lambda: _paris_time(2026, 3, 19))
    assert tracker.state["has_bought_this_month"] is False
    assert tracker.state["monthly_action_count"] == 0
    assert tracker.state["accumulated_budget_multiplier"] == 1.0

def test_state_record_buy(temp_state_file):
    tracker = StateTracker(data_path=str(temp_state_file), now_fn=lambda: _paris_time(2026, 3, 19))
    tracker.state["accumulated_budget_multiplier"] = 2.0
    tracker.record_action("BUY", 8.5, 50000, budget_multiplier_used=2.0)
    
    assert tracker.state["has_bought_this_month"] is True
    assert tracker.state["monthly_action_count"] == 1
    assert tracker.state["accumulated_budget_multiplier"] == 1.0
    assert len(tracker.state["history"]) == 1
    assert tracker.state["history"][0]["type"] == "BUY"
    assert tracker.state["history"][0]["budget_multiplier_used"] == 2.0

def test_state_record_partial_buy_carries_remaining_budget(temp_state_file):
    tracker = StateTracker(data_path=str(temp_state_file), now_fn=lambda: _paris_time(2026, 3, 19))
    tracker.state["accumulated_budget_multiplier"] = 2.0
    tracker.record_action("PARTIAL_BUY", 57.0, 50000, budget_multiplier_used=0.5)

    assert tracker.state["has_bought_this_month"] is False
    assert tracker.state["monthly_action_count"] == 1
    assert tracker.state["accumulated_budget_multiplier"] == 1.5
    assert tracker.state["history"][0]["type"] == "PARTIAL_BUY"

def test_month_rollover_no_buy(temp_state_file):
    # Setup state as if it was last month and we didn't buy
    last_month = "2026-02"
    initial_state = {
        "current_month": last_month,
        "has_bought_this_month": False,
        "monthly_action_count": 0,
        "accumulated_budget_multiplier": 1.0,
        "last_action_date": None,
        "history": []
    }
    with open(temp_state_file, "w") as f:
        json.dump(initial_state, f)
        
    tracker = StateTracker(data_path=str(temp_state_file), now_fn=lambda: _paris_time(2026, 3, 19))
    tracker.update_for_new_month()
    
    # Budget should accumulate
    assert tracker.state["accumulated_budget_multiplier"] == 2.0
    assert tracker.state["current_month"] != last_month
    assert tracker.state["has_bought_this_month"] is False
    assert tracker.state["monthly_action_count"] == 0

def test_month_rollover_after_buy(temp_state_file):
    # Setup state as if it was last month and we DID buy
    last_month = "2026-02"
    initial_state = {
        "current_month": last_month,
        "has_bought_this_month": True,
        "monthly_action_count": 1,
        "accumulated_budget_multiplier": 1.0,
        "last_action_date": None,
        "history": []
    }
    with open(temp_state_file, "w") as f:
        json.dump(initial_state, f)
        
    tracker = StateTracker(data_path=str(temp_state_file), now_fn=lambda: _paris_time(2026, 3, 19))
    tracker.update_for_new_month()
    
    # Budget should RESET/STAY at 1.0 because we bought last month
    assert tracker.state["accumulated_budget_multiplier"] == 1.0
    assert tracker.state["has_bought_this_month"] is False
    assert tracker.state["monthly_action_count"] == 0
