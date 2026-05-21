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
AI_PROVIDER="${AI_PROVIDER:-codex}"
AI_TIMEOUT_SECONDS="${AI_TIMEOUT_SECONDS:-600}"
PROMPT_FILE="src/strategy/ai_deduction_prompt.md"

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

RUN_DIR_REL="outputs/weekly/$RUN_DATE"
RUN_DIR="$PROJECT_ROOT/$RUN_DIR_REL"
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

if [ "$RERUN" = true ] && [ "$DRY_RUN" = false ]; then
  rm -f "$RUN_DIR/sent_discord.ok"
fi

# --- Execution Pipeline ---

# Stage 1: Generate Raw JSON
echo "[$(date -u)] Stage 1: Generating raw report..."
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 src/main.py --json --output-dir $RUN_DIR"
  echo '{"timestamp": "'$(date -u)'", "raw_results": [], "v3_recommendation": {"action": "HOLD", "confidence": 0, "summary": "DRY RUN MOCK"}}' > "$RUN_DIR/weekly_report.json"
else
  docker compose run --rm app python3 src/main.py --json --output-dir "$RUN_DIR_REL"
fi

# Stage 2: Sanitize Data
echo "[$(date -u)] Stage 2: Sanitizing data..."
docker compose run --rm app python3 scripts/sanitize_weekly_report.py \
  --input "$RUN_DIR_REL/weekly_report.json" \
  --output "$RUN_DIR_REL/weekly_report_sanitized.json"

# Stage 3: AI Deduction (Search + Synthesis)
AI_INSIGHT_REL="$RUN_DIR_REL/ai_insight.md"
AI_INSIGHT="$RUN_DIR/ai_insight.md"
AI_STDERR_REL="$RUN_DIR_REL/ai_deduction.stderr.log"
AI_STDERR="$RUN_DIR/ai_deduction.stderr.log"

if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 scripts/run_ai_deduction.py --provider $AI_PROVIDER --input $RUN_DIR_REL/weekly_report_sanitized.json"
  echo "# Dry Run Insight (AI Deduction)" > "$AI_INSIGHT"
  cp "$AI_INSIGHT" "$RUN_DIR/gemini_insight.md" # Temporary compatibility artifact.
else
  echo "[$(date -u)] Stage 3: AI Interpretation & Research via $AI_PROVIDER..."
  python3 scripts/run_ai_deduction.py \
    --provider "$AI_PROVIDER" \
    --project-root "$PROJECT_ROOT" \
    --prompt-file "$PROJECT_ROOT/$PROMPT_FILE" \
    --input "$PROJECT_ROOT/$RUN_DIR_REL/weekly_report_sanitized.json" \
    --mode "$AI_MODE" \
    --output "$AI_INSIGHT" \
    --stderr-log "$AI_STDERR" \
    --timeout-seconds "$AI_TIMEOUT_SECONDS" || {
      echo "[WARNING] AI deduction failed. Using fallback."
      : > "$AI_INSIGHT"
    }
  if [ -s "$AI_INSIGHT" ]; then
    cp "$AI_INSIGHT" "$RUN_DIR/gemini_insight.md" # Temporary compatibility artifact.
  fi
fi

# Stage 4: Discord Push
echo "[$(date -u)] Stage 4: Discord delivery..."
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would run: python3 src/output/send_insight.py --mode insight --input $AI_INSIGHT"
else
  if [ -s "$AI_INSIGHT" ]; then
    docker compose run --rm app python3 src/output/send_insight.py --mode insight --input "$AI_INSIGHT_REL" --validated-json "$RUN_DIR_REL/weekly_report_sanitized.json"
    touch "$RUN_DIR/sent_discord.ok"
  else
    docker compose run --rm app python3 src/output/send_insight.py --mode fallback_error --stage ai_deduction --validated-json "$RUN_DIR_REL/weekly_report_sanitized.json" --message "AI deduction failed or was skipped."
  fi
fi

echo "[$(date -u)] Orchestration complete for $RUN_DATE."
