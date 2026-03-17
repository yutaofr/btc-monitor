import os
import json
import pytest
from datetime import datetime
from src.state.tracker import StateTracker

@pytest.fixture
def temp_state_file(tmp_path):
    return tmp_path / "test_state.json"

def test_state_init_new_file(temp_state_file):
    tracker = StateTracker(data_path=str(temp_state_file))
    assert tracker.state["has_bought_this_month"] is False
    assert tracker.state["accumulated_budget_multiplier"] == 1.0

def test_state_record_buy(temp_state_file):
    tracker = StateTracker(data_path=str(temp_state_file))
    tracker.record_action("BUY", 8.5, 50000)
    
    assert tracker.state["has_bought_this_month"] is True
    assert tracker.state["accumulated_budget_multiplier"] == 1.0
    assert len(tracker.state["history"]) == 1
    assert tracker.state["history"][0]["type"] == "BUY"

def test_month_rollover_no_buy(temp_state_file):
    # Setup state as if it was last month and we didn't buy
    last_month = "2000-01"
    initial_state = {
        "current_month": last_month,
        "has_bought_this_month": False,
        "accumulated_budget_multiplier": 1.0,
        "last_action_date": None,
        "history": []
    }
    with open(temp_state_file, "w") as f:
        json.dump(initial_state, f)
        
    tracker = StateTracker(data_path=str(temp_state_file))
    # current time is definitely not 2000-01
    tracker.update_for_new_month()
    
    # Budget should accumulate
    assert tracker.state["accumulated_budget_multiplier"] == 2.0
    assert tracker.state["current_month"] != last_month
    assert tracker.state["has_bought_this_month"] is False

def test_month_rollover_after_buy(temp_state_file):
    # Setup state as if it was last month and we DID buy
    last_month = "2000-01"
    initial_state = {
        "current_month": last_month,
        "has_bought_this_month": True,
        "accumulated_budget_multiplier": 1.0,
        "last_action_date": None,
        "history": []
    }
    with open(temp_state_file, "w") as f:
        json.dump(initial_state, f)
        
    tracker = StateTracker(data_path=str(temp_state_file))
    tracker.update_for_new_month()
    
    # Budget should RESET/STAY at 1.0 because we bought last month
    # (Actually the logic in tracker.py says if not has_bought: +=1, else it stays reset)
    assert tracker.state["accumulated_budget_multiplier"] == 1.0
    assert tracker.state["has_bought_this_month"] is False
