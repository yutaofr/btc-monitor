# BTC Monitor: Premium Discord Notification Standard

This document defines the **High-Fidelity Discord Notification Standard** for the BTC Monitor pipeline (v3.0+). It ensures visual excellence, data integrity in restricted environments, and precise market-close synchronization.

## 1. Aesthetic & Signal Design (Discord Embeds)

Notifications must use **Discord Embeds** to create a structured, "Data-First" professional appearance.

### 1.1 Dual-Signal Declaration
BTC Monitor follows a **Dual-Signal** reporting philosophy to differentiate between existing positions and new capital:
- **存量资金信号 (Stock/Position)**: Managed via TADR V3.0 (`Target Allocation %`). Header emoji: 📈 (ADD), 🛡️ (HOLD), 📉 (REDUCE).
- **增量资金信号 (Incremental/Cash)**: Managed via Tactical Timing (`BUY_NOW`). Sub-header emojis: 🚀 (BUY_NOW), ⏳ (STAGGER_BUY), 🛑 (WAIT).

### 1.2 Color-Coded Actions
| Action | Color Code | Context |
| :--- | :--- | :--- |
| **ADD / BUY_NOW** | `0x2ECC71` | Green: Aggressive accumulation or entry. |
| **REDUCE / EXIT** | `0x992D22` | Red: Strategic de-risking or overheated exit. |
| **HOLD / WAIT** | `0x3498DB` | Blue: Neutral market regime or "Do Nothing". |
| **LOCKED / ERROR** | `0xE67E22` | Orange: Circuit breaker active or data failure. |

---

## 2. Infrastructure & Resilience (GHA Optimization)

### 2.1 Multi-Exchange Fallback (451 Restricted Location)
GitHub Action runners are often blocked by Binance Global (HTTP 451). The system **MUST** implement a transparent fallback to maintain zero-downtime signals:
1. **Primary**: `Binance` (Target: `BTC/USDT`).
2. **Fallback 1**: `Kraken` (Auto-translated to `BTC/USD`).
3. **Fallback 2**: `Coinbase` (Auto-translated to `BTC/USD`).

*Implementation: All logic is encapsulated in `BinanceFetcher` to remain zero-intrusive to the engine.*

### 2.2 GitHub Secrets Management
- **`DISCORD_WEBHOOK_URL`**: Target channel webhook URL.
- **`FRED_API_KEY`**: Federal Reserve economic data access.
- **`BINANCE_API_KEY`**: (Optional) For high-frequency fetching, though public data is preferred.

---

## 3. Global Scheduling & Precision Guard

### 3.1 Market Close Synchronization (15:45 ET)
To synchronize with the **Nasdaq market close**, the pipeline runs 15 minutes prior (15:45 Eastern Time). This is handled via a **Dual-Cron & Python Guard** pattern in `.github/workflows/discord-notify.yml`:

- **Cron Triggers**: `45 19,20 * * 1-5` (covering EDT and EST shifts).
- **Python Precision Check**: 
```python
import pytz
from datetime import datetime
et_tz = pytz.timezone('US/Eastern')
now_et = datetime.now(et_tz)
# Windows check [15:40, 15:55] ET
is_target = (now_et.hour == 15 and 40 <= now_et.minute <= 55)
```

---

## 4. Implementation Checklist (PR Audit)

- [ ] **Rich Embeds**: No plain text notifications allowed.
- [ ] **Emoji Scannability**: Use emojis (📈, 💰, 🎯) to distinguish Stock from Incremental signals.
- [ ] **Metadata Clarity**: Include `Computation ID` (Timestamp in NS) and `System Multiplier` in the footer.
- [ ] **Zero-Intrusive**: Notification logic must exist as an optional side-effect (`--notify-discord`).

---

> [!TIP]
> **Pro-Tip**: Use the `workflow_dispatch` trigger in the GitHub UI to verify visual rendering before committing to the schedule.
