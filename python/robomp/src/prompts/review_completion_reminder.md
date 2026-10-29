PR review unfinished.

PR: {{repo.full_name}}#{{issue.number}} — {{issue.title}}
Review workspace: `{{workspace.branch}}`

Review started; terminal action not reached.
Incoming PR review terminal action: exactly one:
1. `submit_pr_review` — submit batched review summary plus staged inline comments, with `APPROVE` or `REQUEST_CHANGES`.
2. `abort_task` — unrecoverable environment failure.

Review staged comments, TodoList, prior tool calls; continue from where stopped. Do NOT re-classify unless earlier classify call failed. Do NOT post standalone inline findings. Do NOT run tests, builds, linters, or repo scripts to finish the review — execution belongs to the author and CI. Staged comments → call `submit_pr_review` now with `APPROVE` when no blocking findings remain, otherwise `REQUEST_CHANGES`. The body MUST use the fixed skeleton from the kickoff prompt (`## 结论` / `## 改动核对` / `## 阻塞项` / `## 应改项` / `## 提请注意` / `## 静态核对`, omitting empty sections), written in Chinese. No inline issues → call `submit_pr_review` with `APPROVE` and a 结论 plus 改动核对 only.

MUST end this turn by calling one listed terminal tool.
