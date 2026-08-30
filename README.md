# Skills Hub

Personal skill repository for agent automation.

## Skills

| Category | Skill | Description | Status |
|:--------:|:------|:------------|:------:|
| 🤖 Automation | [real-browser](./skills/real-browser) | Browser automation using real Chrome with CDP | ✅ Active |
| 🖥 Computer Use | [cua-computer-use](./skills/cua-computer-use) | CuaDriver.app + CLI：后台操控本机桌面，或隔离沙箱 | ✅ Active |
| 🔧 Extension | [crxhub-cli](./skills/crxhub-cli) | Manage browser extensions from GitHub Releases | ✅ Active |
| 📦 Package | [npmjs-cli](./skills/npmjs-cli) | Manage npm registry operations and package lifecycle | ✅ Active |
| 🐙 GitHub | [gh-cli](./skills/gh-cli) | GitHub CLI and Git daily dev workflow | ✅ Active |

### cua-computer-use

CuaDriver **在 macOS 上是 App**（`/Applications/CuaDriver.app`），用来拿辅助功能 / 屏幕录制权限并跑守护进程。人和 Agent 日常敲的是旁边的 **`cua-driver` CLI**，不是打开这个 App 去点界面。Windows / Linux 没有这种 GUI App，只有 CLI + 后台 daemon。

人看 [skills/cua-computer-use/README.md](./skills/cua-computer-use/README.md)，Agent 看 [SKILL.md](./skills/cua-computer-use/SKILL.md)。Linux 复跑夹具：`skills/cua-computer-use/tests/linux-smoke.sh`。

```bash
CUA=skills/cua-computer-use/scripts/cua-use
chmod +x "$CUA"
"$CUA" ensure          # 安装 + 拉起 daemon + 列出本机应用
"$CUA" call list_apps
```

macOS 第一次：`"$CUA" grant`（`permissions grant`，不要跑 `cua-driver grant`），再到系统设置里把 CuaDriver 的辅助功能和屏幕录制打开。查权限：`"$CUA" permissions status --json`。

## Installation

```bash
npx skills add https://github.com/xxww0098/skills-hub
```
