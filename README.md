# Skills Hub

Personal skill repository for agent automation.

Installable skills are directories under `skills/` that contain a `SKILL.md`.
**Active** means that contract is present and intended for `npx skills add`.
**Draft** means the folder exists but is not an installable skill.

## Skills

| Category | Skill | Description | Status |
|:--------:|:------|:------------|:------:|
| 🤖 Automation | [real-browser](./skills/real-browser) | Attach agent-browser only to an already-running Chrome with a fixed CDP port | ✅ Active |
| 🖥 Computer Use | [cua-computer-use](./skills/cua-computer-use) | CuaDriver.app + CLI: background-drive the local desktop, or an isolated sandbox | ✅ Active |
| 🔧 Extension | [crxhub-cli](./skills/crxhub-cli) | Install/update/remove browser extensions from GitHub Releases | ✅ Active |
| 📦 Package | [npmjs-cli](./skills/npmjs-cli) | Publish, version, deprecate, and control access on the npm registry | ✅ Active |
| 🐙 GitHub | [gh-cli](./skills/gh-cli) | GitHub CLI + git: PRs, conflicts, Actions, releases | ✅ Active |
| 🌐 Proxy | [charles-cli](./skills/charles-cli) | Charles Proxy as CLI for HTTP/HTTPS capture, export, throttle | ✅ Active |
| 🖼 Branding | [svg2icon](./skills/svg2icon) | SVG logo → Tauri icon set + favicon/branding sync | ✅ Active |
| 🔄 Desktop | [tauri-updater](./skills/tauri-updater) | Tauri v2 auto-update (plugin + sidebar UI + GH Actions `latest.json`) | ✅ Active |
| ⚡ Automation | [n8n-cli](./skills/n8n-cli) | Unfinished stub (no `SKILL.md`, no CLI). Not installable. | 📝 Draft |

`xxww-docs` lives at the repo root (documentation skill), not under `skills/`.

### cua-computer-use

On macOS, CuaDriver is an **App** (`/Applications/CuaDriver.app`) used for
Accessibility / Screen Recording and to run the daemon. Humans and agents type
the **`cua-driver` CLI**, they do not click that App's UI. Windows / Linux have
CLI + background daemon only — no GUI App.

Humans: [skills/cua-computer-use/README.md](./skills/cua-computer-use/README.md).
Agents: [SKILL.md](./skills/cua-computer-use/SKILL.md).
Linux replay (needs `DISPLAY` + `cua-driver`, not GitHub-hosted CI):
`skills/cua-computer-use/tests/linux-smoke.sh`.

```bash
CUA=skills/cua-computer-use/scripts/cua-use
chmod +x "$CUA"
"$CUA" ensure          # install + start daemon (`status`) + list_windows
"$CUA" call list_windows '{"on_screen_only": true}'
```

Liveness is `status`. Never block `ensure` on `list_apps` (macOS hung ~90s
with CuaDriver.app already serving).

First time on macOS: `"$CUA" grant` (`permissions grant`, never
`cua-driver grant`), then enable Accessibility and Screen Recording for
CuaDriver in System Settings. Check: `"$CUA" permissions status --json`.

## Installation

```bash
npx skills add https://github.com/xxww0098/skills-hub
```
