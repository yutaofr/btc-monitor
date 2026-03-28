import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from src.strategy.factor_models import Recommendation
from src.strategy.tadr_engine import TADRInternalState

class DiscordNotifier:
    """
    Premium Discord Notifier for BTC Monitor.
    Aesthetic: High-fidelity Embeds, color-coded status, and structure fields.
    """
    
    COLORS = {
        "ADD": 0x2ECC71,      # Success/Alpha Green
        "REDUCE": 0x992D22,   # Crisis/Exit Red
        "HOLD": 0x3498DB,     # Neutral Blue
        "LOCKED": 0xE67E22    # Warning/Circuit Breaker Orange
    }

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def format_embed(self, recommendation: Recommendation, state: TADRInternalState, current_price: float = 0.0) -> Dict[str, Any]:
        """Builds a rich Discord Embed payload."""
        
        # Determine color and title status
        is_locked = state.is_circuit_breaker_active
        action = recommendation.action
        color = self.COLORS.get("LOCKED" if is_locked else action, 0x3498DB)
        
        status_emoji = "🚨" if is_locked else ("📈" if action == "ADD" else "📉" if action == "REDUCE" else "🛡️")
        title = f"{status_emoji} BTC Monitor V3 Signal: {action}"
        
        description = (
            f"**声明**: 本报告包含 BTC 增量 (Incremental) 与存量 (Stock) 资金信号。建议如下:\n"
            f"> {recommendation.summary}"
        )

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"BTC Monitor Engine v3.0 | Computation ID: {state.computation_timestamp_ns}",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/1490/1490900.png"
            },
            "fields": [
                {
                    "name": "💰 Current Price",
                    "value": f"`${current_price:,.2f}`" if current_price > 0 else "`N/A`",
                    "inline": True
                },
                {
                    "name": "📊 Target Allocation",
                    "value": f"`{state.target_allocation:.1%}`",
                    "inline": True
                },
                {
                    "name": "🎯 Confidence",
                    "value": f"`{state.confidence:.2f}`",
                    "inline": True
                },
                {
                    "name": "🏛️ Strategic Regime",
                    "value": f"`{recommendation.strategic_regime}`",
                    "inline": True
                },
                {
                    "name": "⚡ Tactical State",
                    "value": f"`{recommendation.tactical_state}`",
                    "inline": True
                },
                {
                    "name": "🚦 System Multiplier",
                    "value": f"`{min(state.redundancy_multipliers.values()):.2f}x`" if state.redundancy_multipliers else "`1.00x`",
                    "inline": True
                }
            ]
        }

        # Add support/blocked factors if noteworthy
        if recommendation.supporting_factors:
            embed["fields"].append({
                "name": "✅ Supporting Evidence",
                "value": ", ".join([f"`{f}`" for f in recommendation.supporting_factors[:5]]),
                "inline": False
            })
            
        if is_locked:
            embed["fields"].append({
                "name": "⚠️ Circuit Breaker Active",
                "value": "System gate locked due to critical data failure/redundancy loss.",
                "inline": False
            })

        return embed

    def send(self, recommendation: Recommendation, state: TADRInternalState, current_price: float = 0.0) -> bool:
        """Sends the notification to Discord."""
        if not self.webhook_url:
            return False
            
        embed = self.format_embed(recommendation, state, current_price)
        payload = {
            "username": "BTC Monitor AI Core",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/825/825540.png",
            "embeds": [embed]
        }
        
        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload), 
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False

def send_discord_signal(recommendation: Recommendation, state: TADRInternalState, current_price: float, webhook_url: str):
    notifier = DiscordNotifier(webhook_url)
    notifier.send(recommendation, state, current_price)
