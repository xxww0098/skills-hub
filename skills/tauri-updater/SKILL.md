---
name: tauri-updater
description: >
  Add Tauri v2 auto-update: plugin, sidebar notification UI, and GitHub
  Actions latest.json. Use when the user mentions auto-update, self-update,
  tauri updater, tauri-plugin-updater, update notification, latest.json,
  signed GitHub Releases, or wants a desktop app to check, download, and
  install updates.
---

# Tauri v2 auto-updater

GitHub Release (`v*` tag) → CI `latest.json` → `tauri-plugin-updater` →
`useUpdater` → sidebar bar (no modal). Backend is plugin registration only.

Copy templates from `references/` (`useUpdater.ts`, `UpdateBar.tsx`,
`release.yml`, `build_merged_latest_json.cjs`). Do not invent a parallel API.

## Preconditions

Confirm before editing:

1. Tauri v2 in `src-tauri/Cargo.toml` (`tauri = { version = "2", ... }`)
2. React entry (`src/App.tsx` or equivalent) and `@tauri-apps/api`
3. A sidebar/nav to host the bar (`src/components/layout/` or similar)

If any are missing, ask. Do not force this layout onto a non-React app.

## Implement

**Rust deps** — desktop-only. `cargo add` then move under the cfg block so
mobile builds do not pull the updater:

```toml
[target.'cfg(any(target_os = "macos", windows, target_os = "linux"))'.dependencies]
tauri-plugin-updater = "2.10.0"
tauri-plugin-process = "2.3.1"
```

```bash
cd src-tauri && cargo add tauri-plugin-updater@2.10.0 tauri-plugin-process@2.3.1
```

**tauri.conf.json** — `bundle.createUpdaterArtifacts: true`, plus:

```json
"plugins": {
  "updater": {
    "pubkey": "PLACEHOLDER_GENERATE_WITH_SIGNER",
    "endpoints": [
      "https://github.com/OWNER/REPO/releases/latest/download/latest.json"
    ]
  }
}
```

Add `https://github.com` (and `https://api.github.com` if needed) to CSP
`connect-src` or the check is silently blocked.

**lib.rs** — register only on desktop:

```rust
#[cfg(desktop)]
{
    builder = builder
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init());
}
```

**Frontend**

```bash
npm install @tauri-apps/plugin-updater @tauri-apps/plugin-process
```

Write `src/hooks/useUpdater.ts` from `references/useUpdater.ts`. Why this
shape: check/download/install stay in the hook; `localStorage` holds
`skipped_version` and `last_check` so Rust needs no custom commands. Dynamic
import `check` and `relaunch`. States: `idle | checking | available |
downloading | ready | error`. Auto-check on mount (if interval elapsed) and hourly.

Mount `references/UpdateBar.tsx` under the sidebar logo. Wire from `App.tsx`:

| State | UI | Action |
|-------|----|--------|
| `available` | version + 更新 | `download` |
| `downloading` | percent | none |
| `ready` | 重启 | `apply` (install + relaunch) |
| `error` | truncated error + 重试 | `download` |

**CI** — `.github/workflows/release.yml` from `references/release.yml`, and
`scripts/release/build_merged_latest_json.cjs` from the matching reference.

Jobs: matrix build (macOS arm64/x64, Linux x64, Windows x64) via
`tauri-apps/tauri-action@v0` → merge per-platform signatures into
`latest.json` → publish the draft as latest.

## User must finish (signing)

The skill cannot mint their keys:

1. `npx @tauri-apps/cli signer generate -w ~/.tauri/<app-name>.key`
2. Put the base64 **public** key in `plugins.updater.pubkey`
3. Replace `OWNER/REPO` in the endpoint
4. Repo secret `TAURI_SIGNING_PRIVATE_KEY` = private key file contents
5. `CHANGELOG.md` (CI reads notes from it)
6. First ship: `git tag v0.1.0 && git push origin v0.1.0`

## Verify / traps

`npx tsc --noEmit` · `cargo check` in `src-tauri/` · `npm run build` ·
`npm run tauri build` should emit `.sig` next to artifacts.

| Symptom | Why |
|---------|-----|
| Cannot find plugin module | `npm install` |
| Plugin missing at compile | dep is in the cfg block, not `[dependencies]` |
| No `.sig` | `createUpdaterArtifacts` not under `bundle` |
| `check()` is null | pubkey ≠ CI signing key |
| Check blocked | CSP `connect-src` missing GitHub |
