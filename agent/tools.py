"""Tool abstractions for environment-aware agent actions."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    data: Any
    message: str = ""


class ReadLogTool:
    def run(self, log_path: Path) -> ToolResult:
        if not log_path.exists():
            return ToolResult(False, "", f"Log file not found: {log_path}")
        return ToolResult(True, log_path.read_text(encoding="utf-8"), "")


class ReadCodeTool:
    def run(self, code_path: Path) -> ToolResult:
        if not code_path.exists():
            return ToolResult(False, "", f"Code file not found: {code_path}")
        return ToolResult(True, code_path.read_text(encoding="utf-8"), "")


class RunTestTool:
    def run(self, workdir: Path) -> ToolResult:
        proc = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        return ToolResult(proc.returncode == 0, proc.stdout + proc.stderr, "")


class GitCommitTool:
    def run(self, workdir: Path, message: str) -> ToolResult:
        def _run(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=workdir,
                capture_output=True,
                text=True,
                check=False,
            )

        add_proc = _run("add", ".")
        if add_proc.returncode != 0:
            return ToolResult(False, add_proc.stderr, "git add failed")

        commit_proc = _run("commit", "-m", message)
        if commit_proc.returncode != 0:
            return ToolResult(False, commit_proc.stdout + commit_proc.stderr, "git commit failed")

        sha_proc = _run("rev-parse", "HEAD")
        if sha_proc.returncode != 0:
            return ToolResult(False, sha_proc.stderr, "git rev-parse failed")

        return ToolResult(True, sha_proc.stdout.strip(), "")


class FeishuNotifier:
    """Creates a Feishu card payload. Network delivery is optional."""

    def build_card(self, bug_summary: str, pr_title: str) -> dict[str, Any]:
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "blue",
                    "title": {"tag": "plain_text", "content": "🤖 Agent 自动修复通知"},
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": (
                            "我发现了一个 Bug 并已为您修复，请 Review。\n"
                            f"- Bug: {bug_summary}\n"
                            f"- PR: {pr_title}"
                        ),
                    }
                ],
            },
        }

    def write_preview(self, output_path: Path, payload: dict[str, Any]) -> None:
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")