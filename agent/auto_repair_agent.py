"""Agent workflow for autonomous bug detection and repair."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent.llm_analyzer import TracebackAnalyzer
from agent.tools import FeishuNotifier, GitCommitTool, GitPRTool, ReadCodeTool, ReadLogTool, RunTestTool, WriteCodeTool


@dataclass(frozen=True)
class RepairOutcome:
    fixed: bool
    bug_summary: str
    commit_sha: str
    pr_result: str
    record_path: str
    notification_result: str


class AutoRepairAgent:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.read_log = ReadLogTool()
        self.read_code = ReadCodeTool()
        self.write_code = WriteCodeTool()
        self.run_test = RunTestTool()
        self.git_commit = GitCommitTool()
        self.git_pr = GitPRTool()
        self.notifier = FeishuNotifier()
        self.analyzer = TracebackAnalyzer()

    def repair_from_log(self, log_path: Path) -> RepairOutcome:
        log_result = self.read_log.run(log_path)
        if not log_result.ok:
            raise RuntimeError(log_result.message)

        plan = self.analyzer.analyze(log_result.data)
        target = self.repo_root / plan.target_file

        code_result = self.read_code.run(target)
        if not code_result.ok:
            raise RuntimeError(code_result.message)
        if plan.old_snippet not in code_result.data:
            raise RuntimeError(
                "Cannot apply fix: expected snippet not found. "
                "The file may already be fixed or the analyzer returned a stale patch."
            )

        updated_code = code_result.data.replace(plan.old_snippet, plan.new_snippet, 1)
        write_result = self.write_code.run(target, updated_code)
        if not write_result.ok:
            raise RuntimeError(write_result.message)

        test_result = self.run_test.run(self.repo_root)
        if not test_result.ok:
            raise RuntimeError(f"Tests failed after patch:\n{test_result.data}")

        branch_name = f"agent-fix/{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        pr_title = f"fix(agent): auto-fix {plan.bug_summary}"
        pr_body = (
            "## What\n"
            f"Agent auto-fixed bug: {plan.bug_summary}.\n\n"
            "## Root Cause\n"
            "The traceback was analyzed and mapped to a minimal code patch.\n\n"
            "## Validation\n"
            "- python -m unittest discover -s tests -v\n"
        )

        commit_result = self.git_commit.run(
            self.repo_root,
            f"fix(agent): {plan.bug_summary}",
            branch_name=branch_name,
        )
        if not commit_result.ok:
            raise RuntimeError(commit_result.message + "\n" + str(commit_result.data))

        pr_result = self.git_pr.run(self.repo_root, pr_title, pr_body, branch_name)
        pr_url = pr_result.data if isinstance(pr_result.data, str) and pr_result.data.startswith("http") else None
        notify_result = self.notifier.notify(self.repo_root, plan.bug_summary, pr_title, pr_url)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "log_path": str(log_path.relative_to(self.repo_root)),
            "plan": asdict(plan),
            "branch": branch_name,
            "commit_sha": commit_result.data,
            "pr": {"title": pr_title, "body": pr_body, "result": pr_result.data, "message": pr_result.message},
            "notification": {"ok": notify_result.ok, "data": notify_result.data, "message": notify_result.message},
            "test_output": test_result.data,
        }

        record_dir = self.repo_root / "records"
        record_dir.mkdir(parents=True, exist_ok=True)
        record_path = record_dir / f"repair-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        return RepairOutcome(
            fixed=True,
            bug_summary=plan.bug_summary,
            commit_sha=commit_result.data,
            pr_result=str(pr_result.data),
            record_path=str(record_path.relative_to(self.repo_root)),
            notification_result=str(notify_result.data),
        )
