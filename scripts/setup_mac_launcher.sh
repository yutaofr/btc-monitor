#!/bin/bash
# Setup script to install and load the macOS LaunchAgent.

set -euo pipefail

PLIST_NAME="com.antigravity.btc-monitor.daily.plist"
TARGET_DIR="$HOME/Library/LaunchAgents"
SOURCE_PLIST="$(pwd)/scripts/$PLIST_NAME"

echo "Installing BTC Monitor Daily Launcher..."

# 1. Check if source exists
if [ ! -f "$SOURCE_PLIST" ]; then
    echo "Error: $SOURCE_PLIST not found. Run from project root."
    exit 1
fi

# 2. Copy to LaunchAgents
mkdir -p "$TARGET_DIR"
cp "$SOURCE_PLIST" "$TARGET_DIR/"
echo "Copied plist to $TARGET_DIR"

# 3. Load the agent
echo "Loading agent into launchctl..."
launchctl unload "$TARGET_DIR/$PLIST_NAME" 2>/dev/null || true
launchctl load "$TARGET_DIR/$PLIST_NAME"

echo "----------------------------------------------------------------"
echo "Success! The BTC Monitor will run every day at 20:00."
echo "Logs available at: outputs/logs/mac_daily.log"
echo "----------------------------------------------------------------"
launchctl list | grep antigravity || echo "Warning: Agent might not be visible yet."
