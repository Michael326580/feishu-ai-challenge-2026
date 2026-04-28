"""Agent workflow for autonomous bug detection and repair."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent.llm_analyzer import TracebackAnalyzer
from agent.tools import FeishuNotifier, GitCommitTool, ReadCodeTool, ReadLogTool, RunTestTool


@dataclass
class RepairOutcome:
    fixed: bool
    bug_summary: str
    commit_sha: str
    pr_title: str
    pr_body: str
    record_path: str


class AutoRepairAgent:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.read_log = ReadLogTool()
        self.read_code = ReadCodeTool()
        self.run_test = RunTestTool()
        self.git_commit = GitCommitTool()
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
            raise RuntimeError("Cannot apply fix: expected snippet not found.")

        updated_code = code_result.data.replace(plan.old_snippet, plan.new_snippet)
        target.write_text(updated_code, encoding="utf-8")

        test_result = self.run_test.run(self.repo_root)
        if not test_result.ok:
            raise RuntimeError(f"Tests failed after patch:\n{test_result.data}")

        pr_title = f"fix(agent): auto-fix {plan.bug_summary}"
        pr_body = (
            "## What\n"
            f"Agent auto-fixed bug: {plan.bug_summary}.\n\n"
            "## Why\n"
            "Detected from traceback and mapped by analyzer rule.\n\n"
            "## Validation\n"
            "- python -m unittest discover -s tests -v\n"
        )

        commit_result = self.git_commit.run(
            self.repo_root,
            f"fix(agent): {plan.bug_summary}",
        )
        if not commit_result.ok:
            raise RuntimeError(commit_result.message + "\n" + str(commit_result.data))

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "plan": asdict(plan),
            "commit_sha": commit_result.data,
            "pr": {"title": pr_title, "body": pr_body},
            "test_output": test_result.data,
        }

        record_dir = self.repo_root / "records"
        record_dir.mkdir(parents=True, exist_ok=True)
        record_path = record_dir / f"repair-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        card = self.notifier.build_card(plan.bug_summary, pr_title)
        self.notifier.write_preview(self.repo_root / "records" / "latest_feishu_card.json", card)

        return RepairOutcome(
            fixed=True,
            bug_summary=plan.bug_summary,
            commit_sha=commit_result.data,
            pr_title=pr_title,
            pr_body=pr_body,
            record_path=str(record_path.relative_to(self.repo_root)),
        )