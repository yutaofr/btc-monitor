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
    assert cmd[:3] == ["codex", "--search", "exec"]
    assert "--ephemeral" in cmd
    assert "--output-last-message" in cmd
    assert cwd == str(tmp_path)
    assert timeout == 30


def test_unsupported_provider_writes_error(tmp_path):
    prompt_file, report_file = write_inputs(tmp_path)
    stderr_log = tmp_path / "stderr.log"

    code = run_ai_deduction.run(
        provider="gemini",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=tmp_path / "out.md",
        stderr_log=stderr_log,
        timeout_seconds=30,
    )

    assert code == 2
    assert "Unsupported AI provider" in stderr_log.read_text(encoding="utf-8")


def test_missing_codex_returns_127(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    stderr_log = tmp_path / "stderr.log"
    monkeypatch.setattr(run_ai_deduction.shutil, "which", lambda name: None)

    code = run_ai_deduction.run(
        provider="codex",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=tmp_path / "out.md",
        stderr_log=stderr_log,
        timeout_seconds=30,
    )

    assert code == 127
    assert "not found" in stderr_log.read_text(encoding="utf-8")


def test_codex_timeout_returns_124(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    stderr_log = tmp_path / "stderr.log"

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(run_ai_deduction.shutil, "which", lambda name: "/opt/homebrew/bin/codex")
    monkeypatch.setattr(run_ai_deduction.subprocess, "run", fake_run)

    code = run_ai_deduction.run(
        provider="codex",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=tmp_path / "out.md",
        stderr_log=stderr_log,
        timeout_seconds=1,
    )

    assert code == 124
    assert "timed out" in stderr_log.read_text(encoding="utf-8")


def test_codex_nonzero_preserves_stderr(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    stderr_log = tmp_path / "stderr.log"

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 9, stdout="", stderr="auth failed\n")

    monkeypatch.setattr(run_ai_deduction.shutil, "which", lambda name: "/opt/homebrew/bin/codex")
    monkeypatch.setattr(run_ai_deduction.subprocess, "run", fake_run)

    code = run_ai_deduction.run(
        provider="codex",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=tmp_path / "out.md",
        stderr_log=stderr_log,
        timeout_seconds=30,
    )

    assert code == 9
    assert "auth failed" in stderr_log.read_text(encoding="utf-8")


def test_empty_codex_output_fails(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    output_file = tmp_path / "out.md"
    stderr_log = tmp_path / "stderr.log"

    def fake_run(cmd, **kwargs):
        output_file.write_text("   \n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(run_ai_deduction.shutil, "which", lambda name: "/opt/homebrew/bin/codex")
    monkeypatch.setattr(run_ai_deduction.subprocess, "run", fake_run)

    code = run_ai_deduction.run(
        provider="codex",
        project_root=tmp_path,
        prompt_file=prompt_file,
        report_file=report_file,
        mode="On-demand Insight",
        output_file=output_file,
        stderr_log=stderr_log,
        timeout_seconds=30,
    )

    assert code == 1
    assert "empty output" in stderr_log.read_text(encoding="utf-8")


def test_main_passes_cli_args_to_run(tmp_path, monkeypatch):
    prompt_file, report_file = write_inputs(tmp_path)
    output_file = tmp_path / "out.md"
    stderr_log = tmp_path / "stderr.log"
    received = {}

    def fake_run(**kwargs):
        received.update(kwargs)
        return 0

    monkeypatch.setattr(run_ai_deduction, "run", fake_run)

    code = run_ai_deduction.main(
        [
            "--provider", "codex",
            "--project-root", str(tmp_path),
            "--prompt-file", str(prompt_file),
            "--input", str(report_file),
            "--mode", "On-demand Insight",
            "--output", str(output_file),
            "--stderr-log", str(stderr_log),
            "--timeout-seconds", "7",
        ]
    )

    assert code == 0
    assert received["timeout_seconds"] == 7
    assert received["output_file"] == output_file
