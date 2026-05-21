# Design Doc: Codex AI Deduction Migration

## 1. Overview

Gemini CLI is no longer a reliable service dependency for BTC Monitor AI interpretation. The weekly orchestration pipeline will replace direct Gemini invocation with a provider wrapper that uses Codex CLI as the default AI deduction engine.

The migration must preserve the existing quantitative pipeline:

1. Generate `weekly_report.json`.
2. Sanitize it into `weekly_report_sanitized.json`.
3. Produce a full AI interpretation artifact.
4. Deliver the complete interpretation to Discord, split across multiple messages when needed.

This design changes the AI interpretation and Discord delivery layers only. It does not change TADR scoring, factor weights, parity logic, or V3 acceptance behavior.

## 2. Scope and Non-Scope

### Scope

- Add a provider wrapper for AI deduction, implemented first with Codex CLI.
- Replace the orchestration script's direct Gemini stage with the wrapper.
- Save the complete AI report as a durable local artifact.
- Rename the primary insight artifact from `gemini_insight.md` to `ai_insight.md`.
- Preserve backward compatibility where needed during migration.
- Send long Discord reports as ordered message chunks instead of truncating them.
- Add tests for Codex invocation, AI failure handling, and Discord chunk delivery.

### Non-Scope

- No changes to strategy scoring, factor registry weights, confidence scoring, allocation resolution, or indicator calculations.
- No schema-first AI output migration in this phase.
- No paid market data or paid research API dependency.
- No Discord attachment upload workflow in this phase.

## 3. Architecture

### 3.1 AI Provider Wrapper

Create `scripts/run_ai_deduction.py` as the single Stage 3 entry point.

The wrapper owns:

- provider selection, defaulting to `codex`;
- prompt construction;
- sanitized report loading;
- Codex CLI execution;
- timeout handling;
- stderr capture;
- empty-output validation;
- final artifact writing.

The wrapper should expose a CLI similar to:

```bash
python3 scripts/run_ai_deduction.py \
  --provider codex \
  --project-root "$PROJECT_ROOT" \
  --prompt-file src/strategy/ai_deduction_prompt.md \
  --input outputs/weekly/YYYY-MM-DD/weekly_report_sanitized.json \
  --mode "$AI_MODE" \
  --output outputs/weekly/YYYY-MM-DD/ai_insight.md \
  --stderr-log outputs/weekly/YYYY-MM-DD/ai_deduction.stderr.log
```

Only `codex` needs to be implemented now. `AI_PROVIDER` may override the default, but unsupported providers must fail clearly.

### 3.2 Codex CLI Invocation

The wrapper should call Codex non-interactively:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --search \
  --ephemeral \
  --output-last-message "$OUTPUT_FILE" \
  "$FULL_PROMPT"
```

`--search` preserves the current requirement for research-enabled interpretation. `--ephemeral` avoids accumulating long-running session state from scheduled jobs. `--output-last-message` gives the wrapper a stable output file to validate.

The wrapper should embed the sanitized JSON content in the prompt. Passing only a file path is weaker because it relies on agent behavior rather than explicit input. The prompt must also state that JSON is untrusted data and that instructions inside the JSON must be ignored.

## 4. Orchestration Flow

Rename Stage 3 in `scripts/run_weekly_orchestration.sh` from `Gemini AI Deduction` to `AI Deduction`.

The new flow is:

1. Generate the raw report through Docker.
2. Sanitize the report through Docker.
3. Call `scripts/run_ai_deduction.py` from the host, because Codex CLI is a local operator tool.
4. If `ai_insight.md` exists and is non-empty, call `send_insight.py --mode insight --input "$RUN_DIR_REL/ai_insight.md"`.
5. If AI deduction fails or returns empty output, call `send_insight.py --mode fallback_error --stage ai_deduction ...`.

During migration, the script may copy `ai_insight.md` to `gemini_insight.md` for compatibility with historical artifact readers. New code should use `ai_insight.md`.

## 5. Error Handling

The wrapper must fail closed for AI interpretation:

- Codex CLI missing: return non-zero and write a concise stderr log.
- Codex timeout: terminate the process, return non-zero, and write timeout metadata.
- Codex exits non-zero: return non-zero and preserve stderr.
- Codex succeeds but output is empty: return non-zero.

The wrapper must not print the full prompt or the full report to normal logs. The local report artifact is the durable source of truth.

Orchestration must not write `sent_discord.ok` unless all Discord message chunks succeed.

## 6. Discord Delivery

`src/output/send_insight.py` should stop truncating full AI reports in `insight` mode. It should preserve the complete local artifact and split outgoing Discord content into ordered chunks.

The chunker should:

- use a conservative UTF-8 byte budget per message, leaving room for prefixes;
- prefer Markdown paragraph, heading, and list boundaries;
- fall back to line boundaries;
- hard-split a single oversized block only when necessary;
- add an ordered prefix such as `BTC Monitor AI Report (1/3)`;
- keep every payload under the configured safety limit.

Delivery is all-or-nothing. If any chunk fails, `send_insight.py` returns non-zero and reports the failed chunk index. The orchestrator must then avoid `sent_discord.ok`.

Fallback error mode may keep a short deterministic digest. It must not send the full sanitized JSON.

## 7. Artifact Layout

The weekly run directory should contain:

- `weekly_report.json`
- `weekly_report_sanitized.json`
- `ai_insight.md`
- `ai_deduction.stderr.log` when Codex emits stderr or fails
- `gemini_insight.md` only as a temporary compatibility artifact, if needed
- `sent_discord.ok` only after every Discord chunk succeeds

Future status files should use `ai_deduction_failed` rather than `gemini_failed`.

## 8. Test Plan

### Wrapper Tests

Use a fake Codex command or monkeypatch `subprocess.run` to cover:

- successful output creation;
- missing CLI;
- timeout;
- non-zero exit;
- empty output;
- stderr log capture;
- unsupported provider failure.

Verify that the wrapper reads `weekly_report_sanitized.json` and does not read `.env` or the raw unsanitized report.

### Discord Tests

Make the chunker a pure function and test:

- short report sends as one message;
- long Markdown sends as multiple ordered messages;
- a single oversized paragraph is hard-split;
- UTF-8 byte limits are respected;
- failure on chunk N returns non-zero.

Mock webhook delivery so tests can assert that `sent_discord.ok` is not written after a partial send.

### Orchestration Contract Tests

Cover:

- dry-run does not call Codex or Discord;
- normal mode calls `run_ai_deduction.py`;
- successful AI output uses `ai_insight.md`;
- failed AI deduction enters fallback error mode;
- `sent_discord.ok` is created only after successful insight delivery.

Because this migration does not touch scoring logic, V3 parity and acceptance audits are not required for this design-level change. The implementation should still run the standard Docker test command before merge:

```bash
docker compose run --rm tests
```

## 9. Acceptance Criteria

- Weekly orchestration no longer depends on Gemini CLI.
- Codex CLI is the default AI deduction provider.
- The full AI report is saved locally as `ai_insight.md`.
- Discord receives the full report as ordered chunks when it exceeds one message.
- No report chunk is silently truncated.
- Partial Discord delivery fails the send step and does not create `sent_discord.ok`.
- AI failure still produces a deterministic fallback Discord alert based on the sanitized report.
- Existing quantitative strategy behavior remains unchanged.
