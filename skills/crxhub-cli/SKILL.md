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
- **Rust** — only if building from source

## Setup

```bash
cd /Users/xxww/Code/skills-hub/skills/crxhub-cli
cargo build --release
cp target/release/crx scripts/crx
```

The built binary is at `scripts/crx`. Alternatively:

```bash
sudo cp scripts/crx /usr/local/bin/
```

## Commands

### Install

```bash
crx install <owner/repo>                       # latest release, auto-detect asset
crx install <owner/repo> --tag 1.5.6           # specific version
crx install <owner/repo> '*chrome*.zip'        # filter by asset name glob
crx install <owner/repo> --tag v2.0 -y         # specific version, skip prompt
crx <owner/repo>                               # shorthand (infers install)
crx https://github.com/owner/repo              # GitHub URL also works
```

### Update

```bash
crx update <owner/repo>              # update single extension to latest
crx update <owner/repo> 1.5.6       # switch to a specific version
crx update                           # update all installed extensions
```

### Check Outdated

```bash
crx outdate                          # check all
crx outdate <owner/repo>             # check one
```

### Cleanup

Remove old versions, keep only the active one (like `brew cleanup`).

```bash
crx cleanup                          # cleanup all repos
crx cleanup <owner/repo>             # cleanup one repo
crx cleanup --keep 3                 # keep 3 most recent versions
```

### List

```bash
crx list                             # show installed extensions + load paths
```

### Uninstall

```bash
crx uninstall <owner/repo>
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
2. Scores assets to pick the best `.crx` / `.zip` for Chromium (prefers Edge > Chrome > generic; penalizes Firefox/Safari)
3. Downloads, verifies SHA-256 digest (if available), and unpacks
4. Atomically replaces the `current/` directory so the browser picks up new files on reload
5. Old versions are auto-cleaned (keeps 3 most recent) after updates
