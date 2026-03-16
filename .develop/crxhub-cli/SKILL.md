---
name: crxhub-cli
description: Manage browser extensions and plugins from GitHub Releases. Use this skill whenever the user wants to install, update, remove, list, or check versions of browser extensions/crx files. Also handles anything related to the ~/.crxhub-cli directory, extension load paths, or crx CLI commands.
argument-hint: <command> [owner/repo] [args...]
---

# CrxHub Skill — Extension Manager CLI

A Rust CLI (`crx`) that downloads, versions, and manages Chromium browser extensions from GitHub Releases.

## When to Use This Skill

- User asks to **install** a browser extension from a GitHub repo
- User wants to **check for updates** or **upgrade** installed extensions
- User needs to **list** managed extensions or their stable load paths
- User wants to **remove** an extension

## Prerequisites

- **GitHub CLI** (`gh`) — authenticated (`gh auth login`)

## How to Run

Pre-built binaries are in `scripts/` **in the same directory as this SKILL.md**, one per platform:

| File | Platform |
|------|----------|
| `scripts/crx-darwin-arm64` | macOS Apple Silicon |
| `scripts/crx-darwin-x86_64` | macOS Intel |
| `scripts/crx-linux-x86_64` | Linux x86_64 |
| `scripts/crx-windows-x86_64.exe` | Windows x86_64 |

**Detect and use the right binary** — substitute `<SKILL_DIR>` with the directory
containing this SKILL.md, then run:

**macOS / Linux (bash):**
```bash
SKILL_DIR="<SKILL_DIR>"   # e.g. /Users/alice/skills-hub/develop/crxhub-cli
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)  CRX="$SKILL_DIR/scripts/crx-darwin-arm64"  ;;
  Darwin-x86_64) CRX="$SKILL_DIR/scripts/crx-darwin-x86_64" ;;
  Linux-x86_64)  CRX="$SKILL_DIR/scripts/crx-linux-x86_64"  ;;
  *) echo "Unsupported platform: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac
chmod +x "$CRX"
```

**Windows (PowerShell):**
```powershell
$CRX = "<SKILL_DIR>\scripts\crx-windows-x86_64.exe"
```

Then use `$CRX` instead of `crx` in all commands below.

## Commands

### Install

```bash
$CRX install <owner/repo>                       # latest release, auto-detect asset
$CRX install <owner/repo> --tag 1.5.6           # specific version
$CRX install <owner/repo> '*chrome*.zip'        # filter by asset name glob
$CRX install <owner/repo> --tag v2.0 -y         # specific version, skip prompt
$CRX <owner/repo>                               # shorthand (infers install)
$CRX https://github.com/owner/repo              # GitHub URL also works
```

### Update

```bash
$CRX update <owner/repo>              # update single extension to latest
$CRX update <owner/repo> 1.5.6        # switch to a specific version
$CRX update                            # update all installed extensions
```

### Check Outdated

```bash
$CRX outdate                          # check all
$CRX outdate <owner/repo>             # check one
```

### Info

```bash
$CRX info <owner/repo>               # show version, id, load path, disk usage
```

### Cleanup

Remove old versions, keep only the active one (like `brew cleanup`).

```bash
$CRX cleanup                          # cleanup all repos
$CRX cleanup <owner/repo>             # cleanup one repo
$CRX cleanup --keep 3                 # keep 3 most recent versions
```

### List

```bash
$CRX list                             # show installed extensions + load paths
```

### Uninstall

```bash
$CRX uninstall <owner/repo>
```

### Global Flags

| Flag | Description |
|------|-------------|
| `-y`, `--yes` | Auto-select the first matching asset (skip interactive prompt) |
| `-h`, `--help` | Print help |
| `-V`, `--version` | Print version |

## Storage Layout

```
~/.crxhub-cli/
├── registry.json                              # tracks all installed repos
└── extensions/
    └── {owner}/{repo}/
        ├── {tag}/unpacked/                    # versioned archive
        └── current/                           # stable path for browser to load
```

## How It Works

1. Fetches release metadata via `gh release view`
2. Scores assets to pick the best `.crx` / `.zip` for Chromium (prefers Edge > Chrome/Chromium > generic; penalizes Firefox/Safari/Opera)
3. Downloads, verifies SHA-256 digest (if available), and unpacks
4. Atomically replaces the `current/` directory so the browser picks up new files on reload
5. Old versions are auto-cleaned (keeps 3 most recent) after updates
