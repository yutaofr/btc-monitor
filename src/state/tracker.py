import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from src.config import Config

class StateTracker:
    def __init__(self, data_path=None, now_fn=None):
        self.data_path = data_path or Config.DATA_PATH
        self.timezone = ZoneInfo(Config.TIMEZONE)
        self.now_fn = now_fn or (lambda: datetime.now(self.timezone))
        self.state = self._load()

    def _now(self):
        return self.now_fn()

    def _load(self):
        """Load state from file or create default if missing."""
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                state.setdefault("monthly_action_count", 0)
                state.setdefault("history", [])
                return state
        
        # Default state
        now = self._now()
        return {
            "current_month": now.strftime("%Y-%m"),
            "has_bought_this_month": False,
            "monthly_action_count": 0,
            "accumulated_budget_multiplier": 1.0,
            "last_action_date": None,
            "history": []
        }

    def save(self):
        """Save current state to disk."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def update_for_new_month(self):
        """Check if it's a new month and handle budget roll-over."""
        now = self._now()
        month_str = now.strftime("%Y-%m")
        
        if month_str != self.state["current_month"]:
            # If we didn't buy last month, accumulate budget
            if not self.state["has_bought_this_month"]:
                self.state["accumulated_budget_multiplier"] += 1.0
                # Cap it by security principle
                self.state["accumulated_budget_multiplier"] = min(
                    self.state["accumulated_budget_multiplier"], 
                    Config.MAX_BUDGET_MULTIPLIER
                )
            
            # Reset for new month
            self.state["current_month"] = month_str
            self.state["has_bought_this_month"] = False
            self.state["monthly_action_count"] = 0
            self.save()
            return True
        return False

    def record_action(self, action_type, score, price, budget_multiplier_used=0.0, metadata=None):
        """Record a BUY or SIGNAL action."""
        self.state["last_action_date"] = self._now().isoformat()
        if action_type == "BUY":
            self.state["has_bought_this_month"] = True
            self.state["monthly_action_count"] += 1
            # Reset multiplier after a buy
            self.state["accumulated_budget_multiplier"] = 1.0
        elif action_type == "PARTIAL_BUY":
            self.state["monthly_action_count"] += 1
            remaining_budget = self.state["accumulated_budget_multiplier"] - budget_multiplier_used
            self.state["accumulated_budget_multiplier"] = round(max(0.0, remaining_budget), 2)
            
        history_entry = {
            "date": self.state["last_action_date"],
            "type": action_type,
            "score": score,
            "price": price,
            "budget_multiplier_used": budget_multiplier_used,
        }
        if metadata:
            history_entry.update(metadata)

        self.state["history"].append(history_entry)
        self.save()

if __name__ == "__main__":
    tracker = StateTracker()
    print(f"Loaded month: {tracker.state['current_month']}")
    tracker.update_for_new_month()
