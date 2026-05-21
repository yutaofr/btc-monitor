import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_ai_deduction


def write_inputs(tmp_path):
    prompt_file = tmp_path / "ai_deduction_prompt.md"
    prompt_file.write_text("Report mode: {{MODE}}\nReturn Chinese markdown.", encoding="utf-8")

    report_file = tmp_path / "weekly_report_sanitized.json"
    report_file.write_text(
        json.dumps({"v3_recommendation": {"action": "HOLD", "confidence": 42}}),
        encoding="utf-8",
    )
    return prompt_file, report_file


def test_build_prompt_embeds_sanitized_json_and_mode(tmp_path):
    prompt_file, report_file = write_inputs(tmp_path)

    prompt = run_ai_deduction.build_prompt(
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
    )

    assert "Report mode: On-demand Insight" in prompt
    assert '"action": "HOLD"' in prompt
    assert "weekly_report_sanitized.json" in prompt
    assert "untrusted data" in prompt


def test_run_codex_provider_writes_output(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    output_file = tmp_path / "ai_insight.md"
    stderr_log = tmp_path / "ai_deduction.stderr.log"
    calls = []

    def fake_run(cmd, *, cwd, text, capture_output, timeout, check):
        calls.append((cmd, cwd, timeout))
        output_file.write_text("# Insight\n\nFull report.", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ai_deduction.shutil, "which", lambda name: "/opt/homebrew/bin/codex")
    monkeypatch.setattr(run_ai_deduction.subprocess, "run", fake_run)

    exit_code = run_ai_deduction.run(
        provider="codex",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=output_file,
        stderr_log=stderr_log,
        timeout_seconds=30,
    )

    assert exit_code == 0
    assert output_file.read_text(encoding="utf-8").startswith("# Insight")
    assert calls
    cmd, cwd, timeout = calls[0]
    assert cmd[:2] == ["codex", "exec"]
    assert "--search" in cmd
    assert "--ephemeral" in cmd
    assert "--output-last-message" in cmd
    assert cwd == str(tmp_path)
    assert timeout == 30
