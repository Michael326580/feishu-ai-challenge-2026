"""Tool abstractions for environment-aware agent actions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
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


class WriteCodeTool:
    def run(self, code_path: Path, content: str) -> ToolResult:
        code_path.write_text(content, encoding="utf-8")
        return ToolResult(True, str(code_path), "")


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
    def run(self, workdir: Path, message: str, branch_name: str | None = None) -> ToolResult:
        def _run(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=workdir,
                capture_output=True,
                text=True,
                check=False,
            )

        if branch_name:
            checkout = _run("checkout", "-B", branch_name)
            if checkout.returncode != 0:
                return ToolResult(False, checkout.stdout + checkout.stderr, "git checkout failed")

        add_proc = _run("add", ".")
        if add_proc.returncode != 0:
            return ToolResult(False, add_proc.stdout + add_proc.stderr, "git add failed")

        diff_proc = _run("diff", "--cached", "--quiet")
        if diff_proc.returncode == 0:
            sha_proc = _run("rev-parse", "HEAD")
            return ToolResult(True, sha_proc.stdout.strip(), "no staged changes")

        commit_proc = _run("commit", "-m", message)
        if commit_proc.returncode != 0:
            return ToolResult(False, commit_proc.stdout + commit_proc.stderr, "git commit failed")

        sha_proc = _run("rev-parse", "HEAD")
        if sha_proc.returncode != 0:
            return ToolResult(False, sha_proc.stdout + sha_proc.stderr, "git rev-parse failed")

        return ToolResult(True, sha_proc.stdout.strip(), "")


class GitPRTool:
    """Create a GitHub PR when GitHub CLI is available; otherwise write a preview."""

    def run(self, workdir: Path, title: str, body: str, branch_name: str, base: str = "main") -> ToolResult:
        records_dir = workdir / "records"
        records_dir.mkdir(parents=True, exist_ok=True)

        if not shutil.which("gh"):
            preview_path = records_dir / "latest_pr_preview.md"
            preview_path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
            return ToolResult(True, str(preview_path.relative_to(workdir)), "gh not found; wrote PR preview")

        push_proc = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        if push_proc.returncode != 0:
            return ToolResult(False, push_proc.stdout + push_proc.stderr, "git push failed")

        pr_proc = subprocess.run(
            ["gh", "pr", "create", "--base", base, "--head", branch_name, "--title", title, "--body", body],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        if pr_proc.returncode != 0:
            return ToolResult(False, pr_proc.stdout + pr_proc.stderr, "gh pr create failed")

        return ToolResult(True, pr_proc.stdout.strip(), "")


class FeishuNotifier:
    """Build and optionally send a Feishu/Lark interactive card payload."""

    def build_card(self, bug_summary: str, pr_title: str, pr_url: str | None = None) -> dict[str, Any]:
        pr_text = pr_url or pr_title
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "blue",
                    "title": {"tag": "plain_text", "content": "Agent 自动修复通知"},
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": (
                            "我发现了一个 Bug 并已为您修复，请 Review。\n"
                            f"**Bug**：{bug_summary}\n"
                            f"**PR**：{pr_text}"
                        ),
                    }
                ],
            },
        }

    def write_preview(self, output_path: Path, payload: dict[str, Any]) -> ToolResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return ToolResult(True, str(output_path), "")

    def _signed_payload(self, payload: dict[str, Any], secret: str | None) -> dict[str, Any]:
        if not secret:
            return payload
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
        sign = base64.b64encode(hmac.new(string_to_sign, b"", digestmod=hashlib.sha256).digest()).decode("utf-8")
        return {**payload, "timestamp": timestamp, "sign": sign}

    def send_webhook(self, webhook_url: str, payload: dict[str, Any], secret: str | None = None) -> ToolResult:
        data = json.dumps(self._signed_payload(payload, secret), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8")
            return ToolResult(True, body, "")
        except Exception as exc:
            return ToolResult(False, repr(exc), "Feishu webhook delivery failed")

    def notify(self, workdir: Path, bug_summary: str, pr_title: str, pr_url: str | None = None) -> ToolResult:
        payload = self.build_card(bug_summary, pr_title, pr_url)
        preview_path = workdir / "records" / "latest_feishu_card.json"
        self.write_preview(preview_path, payload)

        webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
        if not webhook_url:
            return ToolResult(True, str(preview_path.relative_to(workdir)), "webhook not configured; wrote preview")
        return self.send_webhook(webhook_url, payload, os.getenv("FEISHU_BOT_SECRET"))
