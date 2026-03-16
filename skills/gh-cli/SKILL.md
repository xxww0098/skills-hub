---
name: gh-cli
description: GitHub CLI (gh) + Git daily dev workflow — branching, committing, stash, push conflict resolution, PRs, releases, Actions, extensions, and API.
---

# GitHub CLI & Git 日常开发参考

> 聚焦最常用的开发流程和冲突解决。完整文档：`gh <command> --help`

## 场景导航

| 我想要… | 跳转 |
|---------|------|
| 开始一个新功能 | [日常开发流程](#日常开发流程) |
| 解决 push / merge 冲突 | [Push 冲突解决](#push-冲突解决) |
| 临时切换分支，保存手头工作 | [Stash 暂存](#stash-暂存) |
| 找到某个 commit 引入的 bug | [Bisect 二分排查](#bisect-二分排查) |
| 创建 / 管理 PR | [PR 操作补充](#pr-操作补充) |
| 找竞品和同类项目 | [探索竞品 & 同类项目](#探索竞品--同类项目) |
| 安装 gh 扩展提升效率 | [扩展生态](#扩展生态) |
| 分享代码片段 | [Gist](#gist) |
| 远程开发 | [Codespace](#codespace) |
| gh 命令出问题了 | [排错 & Debug](#排错--debug) |

---

## 认证

```bash
gh auth login                                 # 交互式登录
gh auth login --with-token < token.txt        # CI / 自动化
gh auth status                                # 检查登录状态
gh auth setup-git                             # 配置 git 凭据
export GH_TOKEN=ghp_xxxxxxxxxxxx              # 环境变量方式（优先级最高）

# 多账号 / GitHub Enterprise
gh auth login --hostname github.example.com   # 登录 GHE 实例
gh auth switch                                # 交互式切换账号
gh auth status --hostname github.example.com  # 检查指定 host 的登录状态
```

---

## 日常开发流程

### 1. 创建分支 & 开始开发

```bash
# 从 main 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/my-feature

# 或从 issue 创建分支（自动关联）
gh issue develop 123 --branch feature/issue-123
```

### 2. 提交更改

```bash
git add .                                     # 暂存所有
git add -p                                    # 交互式选择要暂存的片段
git commit -m "feat: add user login"
git commit --amend                            # 修改最近一次 commit 信息
git commit --amend --no-edit                  # 追加文件到上次 commit，不改信息
```

### 3. 推送到远程

```bash
git push                                      # 推送当前分支
git push -u origin feature/my-feature         # 首次推送，设定上游
git push --force-with-lease                   # 安全强推（rebase 后常用）
```

### 4. 创建 PR

```bash
gh pr create --title "feat: user login" --body "Closes #123" --draft
gh pr create --base main --reviewer user1,user2 --labels enhancement

# 自动关联 Issue 的关键词（写在 PR body 中）
# Closes #123 / Fixes #123 / Resolves #123 → 合并时自动关闭对应 issue

# 等 CI 通过后自动合并
gh pr merge 123 --auto --squash --delete-branch
```

### 5. Code Review & 合并

```bash
gh pr review 123 --approve --body "LGTM!"
gh pr merge 123 --squash --delete-branch      # squash 合并 + 删除分支
gh pr merge 123 --rebase --delete-branch      # rebase 合并
gh pr merge 123 --merge --delete-branch       # merge commit 合并
```

---

## Stash 暂存

> 临时保存工作区改动，切换分支处理其他事情后再恢复。

```bash
git stash                                     # 暂存已跟踪文件的改动
git stash push -m "wip: feature X"            # 带描述的暂存（推荐）
git stash push -u -m "wip: with new files"    # 包含未跟踪文件（-u）
git stash push -- path/to/file                # 只暂存指定文件

git stash list                                # 查看所有暂存记录
git stash show stash@{0}                      # 查看某条暂存的文件列表
git stash show -p stash@{0}                   # 查看某条暂存的 diff

git stash pop                                 # 恢复最近的暂存并删除记录
git stash apply stash@{1}                     # 恢复指定暂存，保留记录
git stash drop stash@{0}                      # 删除某条暂存
git stash clear                               # 清空所有暂存（⚠️ 不可恢复）
```

---

## Push 冲突解决

### 场景 A：push 被拒绝（远程有新的 commit）

> 错误信息：`! [rejected] main -> main (non-fast-forward)`

```bash
# 方案 1：rebase（推荐，保持线性历史）
git fetch origin
git rebase origin/main
# 如果有冲突 → 解决后：
git add <冲突文件>
git rebase --continue
# 如果想放弃 rebase：
git rebase --abort
# rebase 完成后推送：
git push

# 方案 2：merge（保留分叉历史）
git fetch origin
git merge origin/main
# 解决冲突后：
git add <冲突文件>
git commit                                    # 自动生成 merge commit
git push
```

### 场景 B：force push 后协作者无法推送

> 你 `--force` 推送后，别人的本地历史跟远程对不上

```bash
# 协作者执行：
git fetch origin
git reset --hard origin/main                  # ⚠️ 丢弃本地未提交更改！

# 更安全的做法——先备份再 reset：
git stash push -m "backup before reset"       # 暂存本地修改
git fetch origin
git reset --hard origin/main
git stash pop                                 # 恢复本地修改，可能需要解决冲突
```

### 场景 C：PR 分支与 base 分支冲突

> GitHub 提示 "This branch has conflicts that must be resolved"

```bash
# 方案 1：rebase onto base branch（推荐）
git checkout feature/my-feature
git fetch origin
git rebase origin/main
# 逐个解决冲突 → git add → git rebase --continue
git push --force-with-lease                   # rebase 后必须强推

# 方案 2：通过 gh cli 更新 PR 分支（GitHub 端 merge）
gh pr update-branch 123

# 方案 3：merge base 进来
git checkout feature/my-feature
git merge origin/main
# 解决冲突 → git add → git commit
git push
```

### 场景 D：amend / rebase 后推送被拒绝

> 你修改了已推送的 commit（amend 或 rebase），本地历史与远程不同

```bash
# 用 --force-with-lease 安全强推
git push --force-with-lease

# ⚠️ 不要用 --force，它不检查远程是否被别人更新过
# --force-with-lease 会在远程有你未见过的新 commit 时拒绝推送
```

### 场景 E：误操作后回退

```bash
# 撤销最近一次 commit（保留文件改动）
git reset --soft HEAD~1

# 撤销最近一次 commit（丢弃文件改动）
git reset --hard HEAD~1

# 找回被 reset 掉的 commit
git reflog                                    # 查看操作历史
git checkout <commit-hash>                    # 或 git cherry-pick <hash>

# 撤销一个已推送的 commit（生成反向 commit）
git revert <commit-hash>
git push
```

### 场景 F：反复遇到相同冲突（长期维护分支）

> 每次 rebase 都要解决同样的冲突？让 git 记住你的解决方式。

```bash
git config --global rerere.enabled true       # 开启 rerere（reuse recorded resolution）
# 之后 git 会自动记住冲突解决方式，下次遇到相同冲突时自动应用
# 查看 rerere 缓存：
git rerere status
git rerere diff
```

### 冲突解决速查

| 场景 | 推荐方案 | 命令 |
|------|---------|------|
| push 被拒（远程有新 commit） | `rebase` | `git fetch && git rebase origin/main && git push` |
| PR 分支过期 | `rebase + force push` | `git rebase origin/main && git push --force-with-lease` |
| amend/rebase 后推不上去 | `--force-with-lease` | `git push --force-with-lease` |
| merge 冲突文件 | 手动解决 | 编辑文件 → `git add` → `git rebase --continue` |
| 想放弃 rebase | abort | `git rebase --abort` |
| 误操作想回退 | reflog | `git reflog` → `git reset --hard <hash>` |
| 反复遇到相同冲突 | rerere | `git config --global rerere.enabled true` |

---

## Bisect 二分排查

> 快速定位"哪个 commit 引入了 bug"——git 自动二分查找。

```bash
git bisect start
git bisect bad                                # 当前版本有 bug
git bisect good v1.0.0                        # 这个版本没问题
# git 自动 checkout 中间的 commit，你测试后标记：
git bisect good                               # 这个版本没问题
git bisect bad                                # 这个版本有问题
# 重复直到找到第一个出问题的 commit
git bisect reset                              # 结束，回到原分支

# 自动化 bisect（用脚本判断好坏）
git bisect start HEAD v1.0.0
git bisect run npm test                       # 测试通过 = good，失败 = bad
```

---

## Repo 管理

```bash
# 创建
gh repo create my-repo --public --description "desc" --license mit
gh repo create org/my-repo --private

# Clone / Fork
gh repo clone owner/repo
gh repo fork owner/repo --clone
gh repo sync                                  # sync fork with upstream

# 设置默认 repo
gh repo set-default owner/repo
gh repo view --web

# 重命名
gh repo rename new-name

# Archive（归档，只读）
gh repo archive owner/repo
```

## Issues

```bash
gh issue create --title "Bug" --body "Steps..." --labels bug --assignee @me
gh issue list --assignee @me --labels bug
gh issue list --search "is:open label:bug sort:updated-desc"
gh issue view 123 --comments
gh issue edit 123 --add-label priority
gh issue close 123 --comment "Fixed in #456"
gh issue reopen 123
gh issue pin 123                              # 置顶 issue
gh issue transfer 123 owner/other-repo        # 转移到其他 repo
```

## PR 操作补充

```bash
# 查看
gh pr list --author @me
gh pr list --search "is:open review:required"
gh pr checkout 123                            # 拉取别人的 PR 到本地
gh pr diff 123
gh pr checks 123 --watch                      # 实时看 CI 状态
gh pr view 123 --comments                     # 看 PR 评论

# Review
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "Please fix"
gh pr review 123 --comment --body "question about line 42"

# 编辑 PR
gh pr edit 123 --title "new title" --add-label hotfix
gh pr edit 123 --add-reviewer user1
gh pr ready 123                               # draft → ready for review

# 关闭 / 重新打开
gh pr close 123
gh pr reopen 123
```

## Releases

```bash
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"
gh release create v1.0.0 --notes-file CHANGELOG.md --draft --prerelease
gh release create v1.0.0 --generate-notes     # 自动生成 release notes
gh release upload v1.0.0 ./build/*.tar.gz
gh release download v1.0.0 --pattern "*.tar.gz" --dir ./downloads
gh release delete v1.0.0 --yes
gh release edit v1.0.0 --draft=false           # 发布草稿
```

## GitHub Actions

```bash
gh run list --workflow ci.yml --limit 10
gh run view <ID> --log
gh run view <ID> --log-failed                 # 只看失败的 job 日志
gh run watch <ID>                             # 实时看日志
gh run rerun <ID>                             # 重跑
gh run rerun <ID> --failed                    # 只重跑失败的 job
gh run cancel <ID>                            # 取消运行中的 workflow
gh run download <ID> --dir ./artifacts

# 手动触发
gh workflow run deploy.yml --ref main -f version=1.0.0

# Secrets & Variables
gh secret set MY_SECRET
gh secret set MY_SECRET --env production      # 环境级 secret
gh secret list
gh variable set MY_VAR --body "value"
gh variable set MY_VAR --body "value" --env production

# Actions Cache
gh cache list                                 # 查看 cache 列表和大小
gh cache delete <key>                         # 清理指定 cache
```

## Gist

```bash
gh gist create file.py                        # 创建私有 gist（默认）
gh gist create file.py --public --desc "snippet description"
gh gist create file1.py file2.js              # 多文件 gist
gh gist list                                  # 列出你的 gist
gh gist view <id>
gh gist edit <id>                             # 编辑已有 gist
gh gist clone <id>                            # clone 到本地
gh gist delete <id>
```

## Codespace

```bash
gh codespace create --repo owner/repo         # 创建 codespace
gh codespace create --repo owner/repo --machine largePremiumLinux
gh codespace list                             # 列出所有 codespace
gh codespace ssh -c <name>                    # SSH 连入
gh codespace code -c <name>                   # 在 VS Code 中打开
gh codespace ports -c <name>                  # 查看端口转发
gh codespace stop -c <name>
gh codespace delete -c <name>
```

## 扩展生态

> `gh extension` 是 gh 的插件系统，社区扩展极大提升生产力。

```bash
gh extension browse                           # 浏览社区扩展
gh extension search <keyword>                 # 搜索扩展
gh extension install <owner/repo>             # 安装
gh extension list                             # 已安装的扩展
gh extension upgrade --all                    # 升级所有扩展
gh extension remove <name>                    # 卸载
```

### 推荐扩展

| 扩展 | 说明 |
|------|------|
| `dlvhdr/gh-dash` | TUI 面板，一屏看 PR / Issue / Repo |
| `github/gh-copilot` | 命令行 Copilot（自然语言 → 命令） |
| `seachicken/gh-poi` | 清理已合并的本地分支 |
| `mislav/gh-branch` | 交互式分支切换 |
| `vilmibm/gh-user-status` | 设置 GitHub 状态 |

## API

```bash
gh api /user
gh api /repos/owner/repo --jq '.stargazers_count'
gh api --method POST /repos/owner/repo/issues \
  --field title="Title" --field body="Body"
gh api graphql -f query='{ viewer { login } }'

# 分页遍历
gh api /repos/owner/repo/issues --paginate --jq '.[].title'

# 查看响应头（rate limit 等）
gh api --include /rate_limit
```

## 探索竞品 & 同类项目

> 用 `gh` 在 GitHub 上快速找到与你项目功能相似的产品，分析竞品。

### 按关键词搜索同类项目

```bash
# 按关键词搜索（按 star 数排序，最受欢迎的在前）
gh search repos "browser extension manager" --sort stars --order desc --limit 20

# 限定语言
gh search repos "cli tool" --language go --sort stars
gh search repos "chrome extension" --language typescript --sort stars

# 按 topic 标签搜索（GitHub 项目标签，比关键词更精准）
gh search repos "topic:chrome-extension" --sort stars --limit 30
gh search repos "topic:vscode-extension topic:ai" --sort stars

# 组合条件：最近更新 + 一定 star 数 = 活跃的项目
gh search repos "stars:>100 pushed:>2025-01-01 language:typescript" --topic chrome-extension --sort stars

# 按 fork 数排序（fork 多 = 开发者参与度高）
gh search repos "topic:package-manager" --sort forks --order desc
```

### 查看项目详情

```bash
# 快速查看 repo 概况（描述、star、fork、语言、license）
gh repo view owner/repo

# JSON 获取关键指标，方便对比
gh repo view owner/repo --json stargazerCount,forkCount,description,licenseInfo,primaryLanguage,updatedAt

# 直接在浏览器打开
gh repo view owner/repo --web

# 读 README（不用 clone 就能看）
gh api /repos/owner/repo/readme --jq '.content' | base64 -d

# 看项目用了哪些语言（技术栈分析）
gh api /repos/owner/repo/languages
```

### 批量对比多个竞品

```bash
# 一次对比多个项目的 star / fork / 更新时间
for repo in owner1/repo1 owner2/repo2 owner3/repo3; do
  echo "=== $repo ==="
  gh repo view "$repo" --json stargazerCount,forkCount,updatedAt,description \
    --jq '"⭐ \(.stargazerCount)  🍴 \(.forkCount)  📅 \(.updatedAt[:10])\n\(.description)"'
  echo
done

# 导出为 JSON 便于进一步分析
gh search repos "topic:web-scraper" --sort stars --limit 50 \
  --json fullName,stargazerCount,forkCount,description,updatedAt,license \
  > competitors.json
```

### 深入分析某个项目

```bash
# 看最近的 release 和版本节奏
gh release list --repo owner/repo --limit 10

# 看最近的 issue 活跃度（社区健康度）
gh issue list --repo owner/repo --state all --limit 20
gh issue list --repo owner/repo --label "bug" --state open     # 多少未关闭 bug？

# 看 PR 合并频率（开发活跃度）
gh pr list --repo owner/repo --state merged --limit 20

# 看贡献者（API）
gh api /repos/owner/repo/contributors --jq '.[0:10] | .[] | "\(.login): \(.contributions) commits"'

# 看项目的 topics 标签（发现相关领域）
gh api /repos/owner/repo/topics --jq '.names[]'
```

### 代码搜索（找实现参考）

```bash
# 搜索特定 API / 库的用法
gh search code "import { Hono }" --extension ts --limit 20
gh search code "chrome.runtime.sendMessage" --extension ts

# 在特定 repo 里搜索
gh search code "WebSocket" --repo owner/repo --extension py
```

## JSON 输出 & jq

```bash
gh pr list --json number,title --jq '.[] | select(.number > 100)'
gh issue list --json number,title,labels \
  --jq '.[] | {number, title, tags: [.labels[].name]}'

# 常用 --json 字段（PR）
# number, title, state, author, url, createdAt, updatedAt,
# headRefName, baseRefName, labels, reviewDecision, mergeable

# 常用 --json 字段（Issue）
# number, title, state, author, url, createdAt, labels, assignees, comments
```

## 排错 & Debug

```bash
# 打印 API 请求 / 响应详情
GH_DEBUG=api gh pr list

# 查看响应头（检查 rate limit）
gh api --include /rate_limit

# 查看当前认证状态和 scopes
gh auth status

# 检查 gh 版本（某些命令需要较新版本）
gh --version

# 常见问题
# "gh: command not found"        → 未安装或不在 PATH 中
# "HTTP 401"                     → token 过期，重新 gh auth login
# "HTTP 403 rate limit"          → 请求太频繁，等待或用 token 认证
# "HTTP 422"                     → 请求参数错误，检查字段名
# "graphql: Resource not accessible" → token 缺少权限 scope
```

## 环境变量

| Variable | Purpose |
|----------|---------|
| `GH_TOKEN` | Auth token（跳过 login） |
| `GH_REPO` | 默认 `owner/repo` |
| `GH_HOST` | GitHub hostname（用于 GHE） |
| `GH_PROMPT_DISABLED` | 禁用交互提示（CI 中常用） |
| `GH_DEBUG` | 设为 `api` 打印请求调试信息 |
| `NO_COLOR` | 禁用彩色输出 |

## Shell Completion

```bash
eval "$(gh completion -s zsh)"                # 加到 ~/.zshrc
eval "$(gh completion -s bash)"               # 加到 ~/.bashrc
```
