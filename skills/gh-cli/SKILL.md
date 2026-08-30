---
name: gh-cli
description: >
  Run GitHub CLI (gh) and git for daily shipping: branches, commits, stash,
  rebase, push rejections, merge conflicts, PRs, issues, releases, Actions
  runs, and repo/code search. Use when the user mentions gh, git push
  rejected, non-fast-forward, rebase conflict, force-with-lease, create or
  merge a PR, gh pr, gh issue, gh run, gh release, gh api, stash, bisect, or
  a failed GitHub Actions run. Load this instead of guessing git/gh flags.
---

# GitHub CLI & git

Prefer `gh` for GitHub objects (PR, issue, release, run, api). Use git for
the working tree. `gh <cmd> --help` beats inventing flags.

## Auth first

```bash
gh auth status || gh auth login
# CI / non-interactive:  gh auth login --with-token < token.txt
# Highest priority:      export GH_TOKEN=...
gh auth setup-git
```

Enterprise: `--hostname github.example.com`. Switch accounts: `gh auth switch`.

## Daily loop

```bash
git checkout main && git pull origin main
git checkout -b feature/my-feature
# or: gh issue develop 123 --branch feature/issue-123

git add -p
git commit -m "feat: add user login"
git push -u origin HEAD
gh pr create --title "feat: user login" --body "Closes #123" --draft
gh pr merge --auto --squash --delete-branch
```

`--force-with-lease` after rebase/amend. Never `--force` unless the user
explicitly wants to overwrite unseen remote commits.

## Push / merge conflicts (why these flags)

**Push rejected (`non-fast-forward`)** — remote moved. Rebase to keep history
linear, then push:

```bash
git fetch origin
git rebase origin/main          # fix files → git add → git rebase --continue
# abort: git rebase --abort
git push
```

Merge instead only when the user wants a merge commit.

**PR conflicts with base** — rebase onto `origin/main`, then
`git push --force-with-lease`. GitHub-side alternative: `gh pr update-branch`.

**Amend/rebase of an already-pushed commit** — `git push --force-with-lease`.
`--force-with-lease` refuses if the remote grew since your last fetch.

**Someone else force-pushed** — stash local work, `git fetch`,
`git reset --hard origin/<branch>`, then `git stash pop`. Hard reset drops
unstashed work.

**Undo** — `git reset --soft HEAD~1` keeps files; `--hard` discards.
Already pushed: `git revert <hash>` (do not rewrite shared history).
Lost commit: `git reflog`. Repeated identical conflicts: `git config --global rerere.enabled true`.

## Stash / bisect

```bash
git stash push -u -m "wip: feature X"     # include untracked
git stash list && git stash show -p
git stash pop                             # or apply stash@{n} to keep the entry

git bisect start HEAD v1.0.0
git bisect run npm test                   # exit 0 = good
git bisect reset
```

## PRs, issues, releases, Actions

```bash
gh pr list --author @me
gh pr checkout 123
gh pr diff 123
gh pr checks 123 --watch
gh pr review 123 --approve --body "LGTM"
gh pr merge 123 --squash --delete-branch
gh pr ready 123                           # draft → ready

gh issue create --title "Bug" --body "..." --label bug --assignee @me
gh issue list --assignee @me
gh issue view 123 --comments
gh issue close 123 --comment "Fixed in #456"

gh release create v1.0.0 --generate-notes
gh release upload v1.0.0 ./dist/*.tar.gz
gh release download v1.0.0 --pattern "*.tar.gz" --dir ./downloads

gh run list --workflow ci.yml --limit 10
gh run view <ID> --log-failed
gh run watch <ID>
gh run rerun <ID> --failed
gh workflow run deploy.yml --ref main -f version=1.0.0
gh secret set MY_SECRET                   # --env production for env secrets
```

PR body keywords `Closes #123` / `Fixes #123` close the issue on merge.

## Search and API

```bash
gh search repos "topic:chrome-extension" --sort stars --limit 20
gh search code "chrome.runtime.sendMessage" --extension ts
gh repo view owner/repo --json stargazerCount,forkCount,description,updatedAt
gh api /repos/owner/repo --jq '.stargazers_count'
gh api --method POST /repos/owner/repo/issues --field title="T" --field body="B"
```

## Debug

`GH_DEBUG=api gh pr list` · `gh api --include /rate_limit` · `gh --version`

| Failure | Cause |
|---------|--------|
| command not found | `gh` not on PATH |
| HTTP 401 | token expired → `gh auth login` |
| HTTP 403 rate limit | wait or authenticate |
| HTTP 422 | bad fields |
| Resource not accessible | missing token scope |

Env: `GH_TOKEN`, `GH_REPO`, `GH_HOST`, `GH_PROMPT_DISABLED=1` (CI), `NO_COLOR`.
