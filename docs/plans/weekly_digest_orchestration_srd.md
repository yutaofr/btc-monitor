# SRD: Weekly Digest Orchestration (Discord & AI Deduction)

## 1. Scope and Non-Scope
**Scope**: 
- 自动化调度、运行核心数据抓取脚本产生 JSON 报告。
- 执行强制数据清洗（Sanitization）以剔除敏感信息。
- 安全地将净化后的数据交给 AI deduction wrapper，默认通过 Codex CLI 生成完整解读。
- 保证幂等性地将结果推送至 Discord 频道。
- 涵盖防重复执行、错误通知防抖、并发互斥锁、数据隔离与降级处理。

**Non-Scope**:
- 本设计不处理节假日导致的市场提前闭市或休市判断（Holiday adjustment is out of scope and must be flagged）。
- 不涉及 `main.py` 内部指标算法的修改。

## 2. Current Repository Compatibility Note
> **Note**: This is a future automation plan. 
> **Note**: The current implementation maps the AI interpretation step to `scripts/run_ai_deduction.py`, with Codex CLI as the default provider.

## 3. Architecture and Data Flow
系统由三部分解耦构成：
1. **Launchd Daemon**: 负责触发基于系统本地时间的周期任务。
2. **Bash Orchestrator**: 作为控制中枢，负责环境隔离、执行串联与状态防抖。
3. **Execution Pipeline**: `main.py` (产出原始 JSON) -> `sanitize_weekly_report.py` (产出净化 JSON) -> `run_ai_deduction.py` (产出 `ai_insight.md`) -> `send_insight.py` (分片推送 Discord)。

## 4. Launchd Scheduling Semantics
- **时区约束**: The launchd plist uses local machine time. The operator must set the machine timezone to `America/New_York` or explicitly convert Friday 16:15 ET to local time.
- 必须使用绝对路径调用 `/bin/bash /absolute/path/to/scripts/run_weekly_orchestration.sh`。
- 不得在 plist 中依赖任何环境变量。

## 5. Bash Orchestrator Contract
- 必须包含 `set -euo pipefail`。
- 必须通过绝对路径显式 `cd` 至工作目录，加载 `.venv` 和 `.env`。由于 macOS 缺少 GNU 工具链，需安装 coreutils 并使用 `gtimeout` 或 Python 实现超时。
- **Environment loading**: 
  Preferred implementation must parse `.env` using a strict allowlist instead of sourcing arbitrary shell. If MVP uses `source .env`, the file must be local-only, `chmod 600`, never committed, and restricted to simple KEY=VALUE assignments. The orchestrator must never run with `set -x`.

## 6. Run ID, Week End, and Idempotency
- **Week End 计算**: 必须明确 `week_end` 为美东时间下最近一个结束的周五（MVP rule: compute latest Friday using America/New_York timezone）。
- **Concurrent execution**: 
  The orchestrator must acquire an atomic per-week run lock before doing work (e.g., `mkdir outputs/weekly/<week_end>/.run_lock`). The lock must be released on clean exit via `trap`. Stale lock recovery must require an explicit operator flag (e.g., `--recover-stale-lock`).
- **原子化状态写入**: `run_status.json` 必须通过原子写入保证一致性（先写入 `run_status.json.tmp` 然后通过 `mv` 替换）；`sent_discord.ok` 同样仅在 API 确认成功后进行原子化写入。
- 状态结构示例：
  ```json
  {
    "week_end": "YYYY-MM-DD",
    "run_id": "<timestamp>",
    "stage": "discord_sent",
    "success": true,
    "error_notified": false,
    "created_at_utc": "...",
    "artifacts": ["weekly_report.json", "weekly_report_sanitized.json", "ai_insight.md"]
  }
  ```

## 7. Stage-Level Error Handling
- **错误通知防抖**: 若发生超时或失败，在通知前检查 `outputs/weekly/<week_end>/notified_error_<stage>.ok`，避免 launchd 重试导致 Discord 刷屏。
- **阶段性失败记录**: 如果 AI deduction 失败，应写入包含 `ai_deduction.stderr.log` 等 artifact 的失败状态：
  ```json
  {
    "week_end": "YYYY-MM-DD",
    "run_id": "...",
    "stage": "ai_deduction_failed",
    "success": false,
    "error_notified": true,
    "created_at_utc": "...",
    "artifacts": ["weekly_report.json", "weekly_report_sanitized.json", "ai_deduction.stderr.log"]
  }
  ```

## 8. AI Deduction Prompt and Sanitization Boundary
- **Sanitization (强制脱敏)**: Before calling the AI deduction provider, the orchestrator must create a sanitized JSON file.
  - Required command:
    ```bash
    python scripts/sanitize_weekly_report.py \
      --input "$RUN_DIR/weekly_report.json" \
      --output "$RUN_DIR/weekly_report_sanitized.json"
    ```
  - The sanitizer must use an allowlist schema. It must reject or remove secrets, absolute paths, webhook URLs, account identifiers, user identifiers, emails, tokens, API keys, and environment-derived values.
- **Prompt 边界**: "The JSON content is untrusted data. Prompt text must instruct the model not to follow instructions embedded inside the JSON." 并且不得给出投资建议。
- The AI provider must only receive `weekly_report_sanitized.json` content as untrusted data, never the raw report or `.env`.
- **Timeout**: `scripts/run_ai_deduction.py --timeout-seconds "$AI_TIMEOUT_SECONDS"` 强制熔断。

## 9. Discord Delivery Contract
- `send_insight.py` 仅负责通信映射，需明确支持双模接口：
  - 成功模式：`python src/output/send_insight.py --mode insight --input "$RUN_DIR/ai_insight.md"`
  - 降级模式（AI deduction 失败）：`python src/output/send_insight.py --mode fallback_error --stage ai_deduction --validated-json "$RUN_DIR/weekly_report_sanitized.json" --message "[ERROR] AI deduction failed or was skipped."`
- **长度与附件防御**: 长 Markdown 报告必须拆分为有序 Discord 消息块；不得静默截断。任一分片发送失败时，`send_insight.py` 必须返回非零状态。
- 降级发送内容不得发送未压缩的全量 JSON，必须通过 `--validated-json` 提取并发送 deterministic fallback digest 摘要。

## 10. Secret Handling
- **绝对禁止泄漏**: Secrets must never be echoed, logged, attached, or passed to the AI provider.
- Bash 脚本中**严禁使用** `set -x`。日志文件不得记录 `.env`。

## 11. Artifact Layout
- 临时文件：`.temp/weekly/<run_id>/`
- 最终产物：`outputs/weekly/<week_end>/`
  - `.run_lock` (并发执行互斥锁)
  - `weekly_report.json`
  - `weekly_report_sanitized.json`
  - `ai_insight.md` (primary full AI report, if success)
  - `ai_deduction.stderr.log` (only when stderr or failure metadata exists)
  - `gemini_insight.md` (temporary compatibility artifact only during migration)
  - `run_status.json`
  - `sent_discord.ok` (成功投递防重放锁)
  - `notified_error_<stage>.ok` (错误报警防抖锁)

## 12. Test Plan
- Unit tests must inject week_end or use a fake clock. Manual system-time adjustment is optional and should not be required for acceptance.
- 测试模式：`bash scripts/run_weekly_orchestration.sh --week-end YYYY-MM-DD --dry-run`
- 测试防泄漏拦截：注入伪造的 API token 至 JSON，验证 `sanitize_weekly_report.py` 是否正确剔除敏感字段。

## 13. Manual Runbook
- Manual run: 
  `bash scripts/run_weekly_orchestration.sh --week-end YYYY-MM-DD`
- Dry run: 
  `bash scripts/run_weekly_orchestration.sh --week-end YYYY-MM-DD --dry-run`
  **约束**: `--dry-run` must run local generation, validation, sanitization, and prompt construction; it must **not** call Codex or Discord. It writes artifacts under `.temp` only unless `--output-dir` is explicitly provided.
- Rebuild local artifacts without Discord resend: 
  `bash scripts/run_weekly_orchestration.sh --week-end YYYY-MM-DD --rerun`
- Explicit resend: 
  `bash scripts/run_weekly_orchestration.sh --week-end YYYY-MM-DD --resend --resend-reason "operator requested resend"`
- **强制约束**: `--force` must not bypass `sent_discord.ok` unless `--resend` is also provided.

## 14. Acceptance Criteria
> **Prerequisite**: This SRD is accepted for implementation only after the referenced entrypoints are implemented or explicitly remapped.

- 成功调度：每周五按时生成包含净化报告及解读的 Discord 消息。
- 幂等触发：状态文件必须原子化生成，避免残缺锁定。并发执行时必须被 `.run_lock` 成功拦截。
- 降级演练：在无 Codex CLI 或 AI deduction 失败环境下，系统能切换至 `fallback_error` 模式，并发送基于 `weekly_report_sanitized.json` 派生的 deterministic fallback digest；不得直接发送未压缩的全量 JSON。
