#!/bin/bash
# Weekly Digest Orchestration (V3 Spec Compliant)
# Contract: set -euo pipefail, absolute paths, idempotency.

set -euo pipefail

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$PROJECT_ROOT"
OUTPUT_BASE="$PROJECT_ROOT/outputs/weekly"
TEMP_BASE="$PROJECT_ROOT/.temp/weekly"
WEEK_END=$(date +%Y-%m-%d) # Default to today, overridden by --week-end
DRY_RUN=false
RERUN=false
GEMINI_CLI="gemini" # Customizable

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --week-end)
      WEEK_END="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --rerun)
      RERUN=true
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

RUN_DIR="$OUTPUT_BASE/$WEEK_END"
LOCK_FILE="$RUN_DIR/.run_lock"

echo "[$(date -u)] Starting orchestration for Week End: $WEEK_END"

# --- Idempotency ---
if [ -f "$LOCK_FILE" ] && [ "$RERUN" = false ]; then
  echo "[WARNING] Run lock exists for $WEEK_END. Use --rerun to overwrite."
  exit 0
fi

mkdir -p "$RUN_DIR"
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# --- Execution Pipeline ---

# Stage 1: Generate Raw JSON
echo "[$(date -u)] Stage 1: Generating raw report..."
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 src/main.py --json --output-dir $RUN_DIR"
  # Create a dummy report for dry-run downstream verification
  echo '{"timestamp": "'$(date -u)'", "raw_results": [], "v3_recommendation": {"action": "HOLD", "confidence": 0, "summary": "DRY RUN MOCK"}}' > "$RUN_DIR/weekly_report.json"
else
  python3 src/main.py --json --output-dir "$RUN_DIR"
fi

# Stage 2: Sanitize Data
echo "[$(date -u)] Stage 2: Sanitizing data..."
python3 scripts/sanitize_weekly_report.py \
  --input "$RUN_DIR/weekly_report.json" \
  --output "$RUN_DIR/weekly_report_sanitized.json"

# Stage 3: Gemini Analysis
echo "[$(date -u)] Stage 3: Gemini interpretation..."
if command -v "$GEMINI_CLI" >/dev/null 2>&1; then
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run: $GEMINI_CLI analyze $RUN_DIR/weekly_report_sanitized.json"
    echo "# Dry Run Insight" > "$RUN_DIR/gemini_insight.md"
  else
    # Simulated Gemini call (replace with real CLI command as per env)
    $GEMINI_CLI analyze "$RUN_DIR/weekly_report_sanitized.json" > "$RUN_DIR/gemini_insight.md" || {
      echo "[ERROR] Gemini analysis failed."
      touch "$RUN_DIR/notified_error_gemini.ok"
    }
  fi
else
  echo "[WARNING] Gemini CLI not found. Skipping Stage 3 interpretation."
  echo "AI Interpretation unavailable (CLI missing)." > "$RUN_DIR/gemini_insight.md"
fi

# Stage 4: Discord Push
echo "[$(date -u)] Stage 4: Discord delivery..."
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 src/output/send_insight.py --mode insight --input $RUN_DIR/gemini_insight.md"
else
  if [ -f "$RUN_DIR/gemini_insight.md" ]; then
    python3 src/output/send_insight.py --mode insight --input "$RUN_DIR/gemini_insight.md"
    touch "$RUN_DIR/sent_discord.ok"
  else
    python3 src/output/send_insight.py --mode fallback_error --stage gemini --validated-json "$RUN_DIR/weekly_report_sanitized.json" --message "Gemini analysis failed or was skipped."
  fi
fi

echo "[$(date -u)] Orchestration complete for $WEEK_END."
