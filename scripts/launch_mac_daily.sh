#!/bin/bash
# Wrapper for macOS LaunchAgent to execute daily BTC Monitor run.
# Contract: Loads environment, handles logging redirection, and calls orchestrator.

set -euo pipefail

# 1. Resolve Project Root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 2. Setup Logging Directory
mkdir -p "$PROJECT_ROOT/outputs/logs"
LOG_FILE="$PROJECT_ROOT/outputs/logs/mac_daily.log"

{
    echo "----------------------------------------------------------------"
    echo "[$(date -u)] LAUNCH_MAC_DAILY: Start"
    
    # 3. Load Environment Variables (API Keys, Discord Webhook)
    if [ -f ".env" ]; then
        echo "[$(date -u)] Loading .env file..."
        export $(grep -v '^#' .env | xargs)
    else
        echo "[WARNING] .env file not found. Secrets may be missing."
    fi

    # 4. Set Python Path and Environment
    export PYTHONPATH="${PYTHONPATH:-}:$PROJECT_ROOT"
    export NON_INTERACTIVE=true
    
    # 5. Run Orchestration
    # Using --rerun to ensure we overwrite if multiple manual runs happened
    echo "[$(date -u)] Triggering run_weekly_orchestration.sh..."
    bash scripts/run_weekly_orchestration.sh --rerun
    
    echo "[$(date -u)] LAUNCH_MAC_DAILY: Success"
} >> "$LOG_FILE" 2>&1
