# Skills Hub

Personal skill repository for agent automation.

Installable skills are directories under `skills/` that contain a `SKILL.md`.
**Active** means that contract is present and intended for `npx skills add`.
**Draft** means the folder exists but is not an installable skill.

## Skills

| Category | Skill | Description | Status |
|:--------:|:------|:------------|:------:|
| 🤖 Automation | [real-browser](./skills/real-browser) | Attach agent-browser only to an already-running Chrome with a fixed CDP port | ✅ Active |
| 🖥 Computer Use | [cua-computer-use](./skills/cua-computer-use) | CuaDriver.app + CLI：后台操控本机桌面，或隔离沙箱 | ✅ Active |
| 🔧 Extension | [crxhub-cli](./skills/crxhub-cli) | Install/update/remove browser extensions from GitHub Releases | ✅ Active |
| 📦 Package | [npmjs-cli](./skills/npmjs-cli) | Publish, version, deprecate, and control access on the npm registry | ✅ Active |
| 🐙 GitHub | [gh-cli](./skills/gh-cli) | GitHub CLI + git: PRs, conflicts, Actions, releases | ✅ Active |
| 🌐 Proxy | [charles-cli](./skills/charles-cli) | Charles Proxy as CLI for HTTP/HTTPS capture, export, throttle | ✅ Active |
| 🖼 Branding | [svg2icon](./skills/svg2icon) | SVG logo → Tauri icon set + favicon/branding sync | ✅ Active |
| 🔄 Desktop | [tauri-updater](./skills/tauri-updater) | Tauri v2 auto-update (plugin + sidebar UI + GH Actions `latest.json`) | ✅ Active |
| ⚡ Automation | [n8n-cli](./skills/n8n-cli) | Unfinished stub (no `SKILL.md`, no CLI). Not installable. | 📝 Draft |

`xxww-docs` lives at the repo root (documentation skill), not under `skills/`.

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
