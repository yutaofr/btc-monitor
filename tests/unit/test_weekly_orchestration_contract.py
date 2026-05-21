from pathlib import Path


SCRIPT = Path("scripts/run_weekly_orchestration.sh")


def script_text():
    return SCRIPT.read_text(encoding="utf-8")


def test_orchestrator_calls_ai_deduction_wrapper():
    text = script_text()

    assert "run_ai_deduction.py" in text
    assert "ai_insight.md" in text
    assert "ai_deduction.stderr.log" in text
    assert "Gemini AI" not in text


def test_orchestrator_allows_research_ai_runtime():
    text = script_text()

    assert 'AI_TIMEOUT_SECONDS="${AI_TIMEOUT_SECONDS:-600}"' in text


def test_orchestrator_uses_ai_deduction_stage_for_fallback():
    text = script_text()

    assert "--stage ai_deduction" in text
    assert "AI deduction failed or was skipped." in text


def test_orchestrator_ai_failure_leaves_zero_byte_insight_for_fallback():
    text = script_text()

    assert ': > "$AI_INSIGHT"' in text
    assert 'echo "" > "$AI_INSIGHT"' not in text


def test_orchestrator_touches_sent_marker_only_after_successful_send():
    text = script_text()

    send_index = text.index("send_insight.py --mode insight")
    touch_index = text.index('touch "$RUN_DIR/sent_discord.ok"')

    assert send_index < touch_index
    assert "docker compose run --rm app python3 src/output/send_insight.py --mode insight" in text


def test_orchestrator_clears_stale_sent_marker_on_real_rerun():
    text = script_text()

    clear_index = text.index('rm -f "$RUN_DIR/sent_discord.ok"')
    send_index = text.index("send_insight.py --mode insight")

    assert '[ "$RERUN" = true ] && [ "$DRY_RUN" = false ]' in text
    assert clear_index < send_index
