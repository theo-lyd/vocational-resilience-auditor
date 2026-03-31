# Git Commands (Project Usage)

## `git status --short`
- Who: any contributor
- What: show concise local change state
- When: before commit/push/rebase
- Where: repository root
- Why: avoid accidental commits and verify scope
- How: `git status --short`
- Alternatives: `git status`, `git diff --name-only`

## `git add <files>`
- Who: contributor preparing a commit
- What: stage selected files
- When: after reviewing edits
- Where: repository root
- Why: commit only intended changes
- How: `git add README.md docs/dashboard-guide.md`
- Alternatives: `git add -p` (interactive), `git add .` (broad)

## `git commit -m "<message>"`
- Who: contributor
- What: create a snapshot with message
- When: after staging coherent changes
- Where: repository root
- Why: preserve history and reviewability
- How: `git commit -m "docs: add dashboard guide"`
- Alternatives: `git commit` (editor), squashed merge in PR workflow

## `git push origin master`
- Who: contributor with push rights
- What: publish local commits to remote branch
- When: after local verification
- Where: repository root with network access
- Why: share changes and trigger CI
- How: `git push origin master`
- Alternatives: `git push --set-upstream origin <branch>`

## `git push --no-verify origin master`
- Who: contributor in environments missing hook deps
- What: push while skipping local git hooks
- When: only when hooks are known-environment blockers
- Where: repository root
- Why: unblock delivery in constrained runtime
- How: `git push --no-verify origin master`
- Alternatives: install missing hook dependencies (preferred), fix hook scripts

## `git branch --show-current`
- Who: contributor
- What: print current branch name
- When: before commit/push
- Where: repository root
- Why: avoid pushing to wrong branch
- How: `git branch --show-current`
- Alternatives: `git status`

## `git diff`
- Who: contributor/reviewer
- What: show unstaged changes
- When: before staging/commit
- Where: repository root
- Why: verify exact line-level edits
- How: `git diff` or `git diff -- <file>`
- Alternatives: `git diff --staged`, IDE diff view
