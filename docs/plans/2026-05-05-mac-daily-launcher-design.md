# Design Doc: macOS Daily Launcher (TADR V3.0)

## 1. Overview
Scaffold a native macOS background service to execute the BTC Monitor orchestration pipeline daily at 20:00, ensuring consistent delivery of market insights to Discord.

## 2. Components

### 2.1 macOS LaunchAgent (`com.antigravity.btc-monitor.plist`)
- **Location**: `~/Library/LaunchAgents/`
- **Schedule**: `StartCalendarInterval` (Hour: 20, Minute: 0)
- **StandardOut/Error**: `outputs/logs/mac_daily.log`
- **Behavior**: Persistent, runs on wake if time was missed.

### 2.2 Shell Wrapper (`scripts/launch_mac_daily.sh`)
- Loads `.env` for API keys and Webhooks.
- Sets `PYTHONPATH`.
- Ensures absolute path resolution for `python3`.
- Calls `run_weekly_orchestration.sh --rerun`.

### 2.3 Discord Dispatcher (`src/output/send_insight.py`)
- Upgraded to use `requests` or `urllib` to send raw Markdown content to Discord.
- Implements `fallback_error` to alert user if data fetching or Gemini analysis fails.

## 3. Data Flow
1. `launchd` triggers at 20:00.
2. Wrapper loads secrets and triggers orchestrator.
3. Pipeline generates report -> sanitizes -> (Optional) Gemini analyzes.
4. Dispatcher sends results to Discord.

## 4. Error Handling
- Failure at any stage triggers a Discord "Service Error" notification with the failing stage name.
- Errors are logged to `outputs/logs/mac_daily.log` for troubleshooting.
