#!/bin/bash
# Weekly Digest Orchestration (V3 Spec Compliant)
# Contract: set -euo pipefail, absolute paths, idempotency.

set -euo pipefail

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$PROJECT_ROOT"
OUTPUT_BASE="$PROJECT_ROOT/outputs/weekly"
TEMP_BASE="$PROJECT_ROOT/.temp/weekly"
RUN_DATE=$(date +%Y-%m-%d)
DRY_RUN=false
RERUN=false
GEMINI_CLI="gemini" # Customizable
PROMPT_FILE="$PROJECT_ROOT/src/strategy/ai_deduction_prompt.md"

# --- Date Context ---
DOW=$(date +%u) # 1=Mon, 5=Fri
if [ "$DOW" -eq 1 ]; then
    AI_MODE="周初开盘展望 (Monday Outlook)"
elif [ "$DOW" -eq 5 ]; then
    AI_MODE="周五收盘复盘 (Friday Recap)"
else
    AI_MODE="即时市场解读 (On-demand Insight)"
fi

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --week-end|--run-date)
      RUN_DATE="$2"
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

RUN_DIR="$OUTPUT_BASE/$RUN_DATE"
LOCK_FILE="$RUN_DIR/.run_lock"

echo "[$(date -u)] Starting orchestration for: $RUN_DATE (Mode: $AI_MODE)"

# --- Idempotency ---
if [ -f "$LOCK_FILE" ] && [ "$RERUN" = false ]; then
  echo "[WARNING] Run lock exists for $RUN_DATE. Use --rerun to overwrite."
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
  echo '{"timestamp": "'$(date -u)'", "raw_results": [], "v3_recommendation": {"action": "HOLD", "confidence": 0, "summary": "DRY RUN MOCK"}}' > "$RUN_DIR/weekly_report.json"
else
  python3 src/main.py --json --output-dir "$RUN_DIR"
fi

# Stage 2: Sanitize Data
echo "[$(date -u)] Stage 2: Sanitizing data..."
python3 scripts/sanitize_weekly_report.py \
  --input "$RUN_DIR/weekly_report.json" \
  --output "$RUN_DIR/weekly_report_sanitized.json"

# Stage 3: Gemini AI Deduction (Search + Synthesis)
if command -v "$GEMINI_CLI" >/dev/null 2>&1; then
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would run: $GEMINI_CLI --prompt \"(Deduction Instructions) for $RUN_DIR/weekly_report_sanitized.json\""
    echo "# Dry Run Insight (AI Deduction)" > "$RUN_DIR/gemini_insight.md"
  else
    echo "[$(date -u)] Stage 3: Gemini AI Interpretation & Research..."
    
    # Prepare the combined prompt
    FULL_PROMPT="请结合以下报告执行深度市场调研并给出最终解读。\n\n报告文件: $RUN_DIR/weekly_report_sanitized.json\n\n分析指令模板:\n$(cat "$PROMPT_FILE" | sed "s/{{MODE}}/$AI_MODE/g")"
    
    # Execute Gemini Agent (echo 1 to bypass tool confirmation if needed, though --prompt might be direct)
    echo 1 | $GEMINI_CLI --prompt "$FULL_PROMPT" --raw-output --accept-raw-output-risk < /dev/null > "$RUN_DIR/gemini_insight.md" 2>/dev/null || {
      echo "[WARNING] Gemini analysis failed. Using fallback."
      echo "" > "$RUN_DIR/gemini_insight.md"
    }
  fi
else
  echo "[WARNING] Gemini CLI not found. Skipping Stage 3 interpretation."
  echo "" > "$RUN_DIR/gemini_insight.md"
fi

# Stage 4: Discord Push
echo "[$(date -u)] Stage 4: Discord delivery..."
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 src/output/send_insight.py --mode insight --input $RUN_DIR/gemini_insight.md"
else
  if [ -s "$RUN_DIR/gemini_insight.md" ]; then
    python3 src/output/send_insight.py --mode insight --input "$RUN_DIR/gemini_insight.md" --validated-json "$RUN_DIR/weekly_report_sanitized.json"
    touch "$RUN_DIR/sent_discord.ok"
  else
    python3 src/output/send_insight.py --mode fallback_error --stage gemini --validated-json "$RUN_DIR/weekly_report_sanitized.json" --message "Gemini analysis failed or was skipped."
  fi
fi

echo "[$(date -u)] Orchestration complete for $RUN_DATE."

