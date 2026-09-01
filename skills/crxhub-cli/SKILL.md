---
name: crxhub-cli
description: >
  Install, update, remove, list, and version-check browser extensions (.crx)
  from GitHub Releases. Use when the user mentions crxhub, crx, Chrome or Edge
  extension from GitHub, 安装扩展, 更新 crx, 删除扩展, outdate, or wants a
  GitHub-released browser extension without the Chrome Web Store.
---

# CrxHub CLI

Requires authenticated `gh`.

Resolve the bundled binary from this SKILL.md's directory and run the user
action in **one** shell call. Do not run `list` / `outdate` first unless asked.

```bash
CRX="<SKILL_DIR>/scripts/crx-$(uname -s | tr A-Z a-z)-$(uname -m)"
chmod +x "$CRX"
```

Published globs (no `linux-aarch64`; do not invent one):
`crx-darwin-arm64`, `crx-darwin-x86_64`, `crx-linux-x86_64`,
`crx-windows-x86_64.exe`. Git Bash `uname` is `MINGW*` / `MSYS*` / `CYGWIN*`,
not `windows`, so that glob will not yield `windows-x86_64`. On Windows use
`scripts/crx-windows-x86_64.exe`.

| Intent | Command |
|--------|---------|
| update all / 更新 crx | `$CRX update` |
| update one / 更新 XX | `$CRX update owner/repo` |
| install / 安装 XX | `$CRX install owner/repo -y` |
| remove / 删除 XX | `$CRX uninstall owner/repo` |
| list / 列出扩展 | `$CRX list` |
| check updates / 检查更新 | `$CRX outdate` |

```bash
$CRX install <owner/repo> -y              # latest, auto-detect asset
$CRX install <owner/repo> --tag 1.5.6 -y  # pin version
$CRX update                               # all installed
$CRX update <owner/repo>
$CRX list
$CRX outdate
$CRX info <owner/repo>
$CRX cleanup                              # keep last 1 version (clap --keep default)
$CRX uninstall <owner/repo>
```

Always pass `-y` on install so the shell cannot hang on a prompt.
