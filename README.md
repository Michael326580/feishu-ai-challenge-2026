# Feishu AI Campus Challenge 2026 - Agent Auto Repair Demo

## Project Goal

Build an Agent that monitors a simple web-service error, reads the traceback log,
analyzes the root cause, modifies code automatically, runs tests, commits the fix,
creates a PR or PR preview, and sends a Feishu/Lark card notification.

## Core Flow

```text
Service Error / Bug Log
        ↓
ReadLogTool
        ↓
TracebackAnalyzer
        ↓
ReadCodeTool + WriteCodeTool
        ↓
RunTestTool
        ↓
GitCommitTool + GitPRTool
        ↓
FeishuNotifier
```

## Local Demo

```bash
python scripts/reset_demo_bug.py
python scripts/generate_bug_log.py
python -m unittest discover -s tests -v   # expected to fail before repair
python run_agent_demo.py                  # agent repairs the bug
python -m unittest discover -s tests -v   # expected to pass after repair
```

## Optional Real Integrations

### Feishu/Lark webhook

Set environment variables before running the demo:

```bash
set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
set FEISHU_BOT_SECRET=your_secret_optional
python run_agent_demo.py
```

If no webhook is configured, the agent writes a preview card to:

```text
records/latest_feishu_card.json
```

### GitHub PR

If GitHub CLI is installed and authenticated:

```bash
gh auth login
python run_agent_demo.py
```

If `gh` is unavailable, the agent writes a PR preview to:

```text
records/latest_pr_preview.md
```

## Deliverables for Competition

- Code repository: Agent workflow, tools, analyzer, tests, repair records.
- Demo video: show failing test/log → run agent → code patch → tests pass → commit/PR preview → Feishu card.
- Records: `records/repair-*.json`, `records/latest_feishu_card.json`, `records/latest_pr_preview.md`.
