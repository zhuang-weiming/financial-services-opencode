# Wealth-Guide End-to-End Cookbook

**Cross-domain questions** requiring Wealth-Guide to dispatch to multiple subagents and compose unified answers.

Each question includes the **expected routing** — the subagents Wealth-Guide should invoke. This serves as a test suite for the routing logic.

## How to use

Start a session with Wealth-Guide:

```bash
opencode --agent wealth-guide
```

Then ask any question from `questions.md`. Wealth-Guide should automatically:
1. Classify the intent (single or multi-domain)
2. Dispatch to the correct subagent(s)
3. Collect and compose the answer
