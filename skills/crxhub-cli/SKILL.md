---
name: crxhub-cli
description: Manage browser extensions from GitHub Releases. Use when user wants to install, update, remove, list, or check versions of browser extensions/crx files.
argument-hint: <command> [owner/repo] [args...]
---

# CrxHub CLI

Requires **GitHub CLI** (`gh`) authenticated.

## How to Run

**Always combine setup + command in ONE shell call.** Replace `<SKILL_DIR>` with this SKILL.md's directory:

```bash
CRX="<SKILL_DIR>/scripts/crx-$(uname -s | tr A-Z a-z)-$(uname -m)" && chmod +x "$CRX" && $CRX update
```

## Quick Workflows

Use the **minimum commands** needed. Do NOT run exploratory commands (list, outdate) before the action unless the user specifically asks.

| User intent | Command (append after `&& $CRX`) |
|---|---|
| "更新 crx" / update all | `update` |
| "更新 XX" / update one | `update owner/repo` |
| "安装 XX" / install | `install owner/repo -y` |
| "删除 XX" / remove | `uninstall owner/repo` |
| "列出扩展" / list | `list` |
| "检查更新" / check updates | `outdate` |

## Commands

```bash
$CRX install <owner/repo> -y              # latest, auto-detect asset
$CRX install <owner/repo> --tag 1.5.6 -y  # specific version
$CRX update                               # update ALL installed
$CRX update <owner/repo>                  # update one
$CRX list                                 # installed extensions + paths
$CRX outdate                              # check for updates
$CRX info <owner/repo>                    # version, path, disk usage
$CRX cleanup                              # remove old versions (keep 3)
$CRX uninstall <owner/repo>
```

**Always pass `-y` on install** to avoid interactive prompts hanging the shell.
