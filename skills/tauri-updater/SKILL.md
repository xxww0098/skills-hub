---
name: tauri-updater
description: >
  Add auto-update functionality to Tauri v2 desktop apps with React/TypeScript frontends.
  Implements tauri-plugin-updater for cross-platform update checking, downloading, and installing,
  plus a non-intrusive update notification UI in the sidebar and a GitHub Actions CI/CD pipeline
  that builds signed releases with a latest.json manifest. Use this skill whenever the user
  mentions "auto update", "auto-update", "self-update", "app update", "update notification",
  "tauri updater", "auto update for my tauri app", "add update functionality", or wants their
  Tauri desktop app to check for and install updates automatically.
---

# Tauri v2 Auto-Updater

Add automatic update capability to a Tauri v2 + React desktop app. The system checks GitHub Releases for new versions, downloads signed update packages, and prompts the user to restart — all through a subtle sidebar notification bar, no modal dialogs.

## Architecture

```
GitHub Release (tag v*)
  └── latest.json (CI auto-generated, per-platform signatures + download URLs)
       └── tauri-plugin-updater (frontend API)
            └── useUpdater hook → Sidebar update notification bar
```

- **Backend**: Only plugin registration (3 lines). No custom Rust modules or commands needed.
- **Frontend**: `useUpdater` hook manages all lifecycle (check/download/install) via `@tauri-apps/plugin-updater` API. State stored in `localStorage`.
- **CI**: GitHub Actions builds multi-platform artifacts, signs them, generates `latest.json`, and publishes the release.

## Prerequisites Check

Before starting, verify these exist in the project:

1. **Tauri v2**: Check `src-tauri/Cargo.toml` for `tauri = { version = "2", ... }`
2. **React frontend**: Check for `src/App.tsx` or similar React entry point
3. **package.json**: Confirm `@tauri-apps/api` is present
4. **Sidebar or equivalent**: Check `src/components/layout/` for a sidebar/navigation component

If any are missing, ask the user to clarify their setup before proceeding.

## Implementation Steps

### Step 1: Add Rust dependencies

Edit `src-tauri/Cargo.toml`. Add these as conditional desktop-only dependencies:

```toml
[target.'cfg(any(target_os = "macos", windows, target_os = "linux"))'.dependencies]
tauri-plugin-updater = "2.10.0"
tauri-plugin-process = "2.3.1"
```

Always use `cargo add` to install:
```bash
cd src-tauri && cargo add tauri-plugin-updater@2.10.0 tauri-plugin-process@2.3.1
```
Then manually move them under the `[target.'cfg(any(...))']` conditional block.

### Step 2: Configure tauri.conf.json

Add to the `bundle` section:
```json
"createUpdaterArtifacts": true
```

Add `plugins` section (or merge into existing):
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

Update CSP if needed — add `https://github.com` to `connect-src`:
```
connect-src 'self' https://api.github.com https://github.com
```

### Step 3: Register plugins in lib.rs

In `src-tauri/src/lib.rs`, refactor the builder to support conditional plugin registration:

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        // ... existing plugins ...

    #[cfg(desktop)]
    {
        builder = builder
            .plugin(tauri_plugin_updater::Builder::new().build())
            .plugin(tauri_plugin_process::init());
    }

    builder
        .invoke_handler(tauri::generate_handler![
            // ... existing commands ...
        ])
        .run(tauri::generate_context!())
        .expect("error while running app");
}
```

### Step 4: Add frontend dependencies

```bash
npm install @tauri-apps/plugin-updater @tauri-apps/plugin-process
```

### Step 5: Create useUpdater hook

Create `src/hooks/useUpdater.ts`. See `references/useUpdater.ts` for the full template. Key design:

- **States**: `idle | checking | available | downloading | ready | error`
- **localStorage**: stores `skipped_version` and `last_check` timestamp — no backend commands needed
- **Auto-check**: on mount (if interval elapsed) + hourly `setInterval`
- **API**: `check()`, `download()`, `apply()` (install + relaunch), `skip()`, `dismiss()`

The hook uses dynamic imports for `@tauri-apps/plugin-updater` (`check`) and `@tauri-apps/plugin-process` (`relaunch`).

### Step 6: Add update notification UI

Integrate into the existing sidebar/navigation component. See `references/UpdateBar.tsx` for the full template.

The notification bar appears below the logo area, only when update status is active:

| State | Visual | Action |
|-------|--------|--------|
| `available` | Blue-tinted bar with version + "更新" button | Click to start download |
| `downloading` | Gray bar with progress percentage + animated bar | Automatic |
| `ready` | Green bar with "重启" button | Click to install & relaunch |
| `error` | Red bar with truncated error + "重试" | Click to retry download |

Use `framer-motion` `AnimatePresence` for smooth slide-in/out transitions.

### Step 7: Wire into App.tsx

In the root component:

```tsx
import { useUpdater } from "./hooks/useUpdater";

function App() {
  const updater = useUpdater();
  return (
    <div className="flex h-screen">
      <Sidebar
        // ... existing props ...
        updateStatus={updater.state.status}
        updateVersion={updater.state.version}
        updateProgress={updater.state.progress}
        updateError={updater.state.error}
        onUpdate={updater.download}
        onRestart={updater.apply}
        onSkip={updater.skip}
        onDismiss={updater.dismiss}
      />
      {/* ... rest of layout ... */}
    </div>
  );
}
```

### Step 8: Set up CI/CD

Create `.github/workflows/release.yml`. See `references/release.yml` for the full template.

The pipeline has 3 jobs:
1. **release**: Matrix build (macOS arm64/x64, Linux x64, Windows x64) using `tauri-apps/tauri-action@v0`
2. **rebuild-latest-json**: Downloads all assets, runs `build_merged_latest_json.cjs`, uploads `latest.json`
3. **publish-release**: Publishes the draft release as latest

Create `scripts/release/build_merged_latest_json.cjs`. See `references/build_merged_latest_json.cjs` for the full template.

### Step 9: Post-implementation manual steps

Tell the user they need to complete these steps:

1. **Generate signing key**:
   ```bash
   npx @tauri-apps/cli signer generate -w ~/.tauri/<app-name>.key
   ```
2. **Fill in pubkey**: Replace the placeholder in `tauri.conf.json` → `plugins.updater.pubkey` with the generated base64 public key
3. **Fill in repo URL**: Replace `OWNER/REPO` in the endpoints with the actual GitHub repository
4. **Add GitHub Secret**: Add `TAURI_SIGNING_PRIVATE_KEY` as a repository secret (content of the private key file)
5. **Create CHANGELOG.md**: The CI expects release notes; a simple changelog file works
6. **First release**:
   ```bash
   git tag v0.1.0 && git push origin v0.1.0
   ```

## Verification

After implementation, verify:

1. **TypeScript compiles**: `npx tsc --noEmit` should pass
2. **Rust compiles**: `cargo check` in `src-tauri/` should pass
3. **Build works**: `npm run build` (frontend) should succeed
4. **Full Tauri build**: `npm run tauri build` should produce signed artifacts with `.sig` files

## Common Issues

- **"Cannot find module '@tauri-apps/plugin-updater'"**: Run `npm install` to install the new dependencies
- **Updater plugin not found at build time**: Ensure the dependency is in the conditional `[target.'cfg(...)]'` block, not the main `[dependencies]`
- **No .sig files generated**: Check `"createUpdaterArtifacts": true` is in the `bundle` section of `tauri.conf.json`
- **Update check returns null**: The `pubkey` must match the signing key used during CI build. Regenerate if needed.
- **CSP blocks update check**: Add `https://github.com` to `connect-src` in the CSP policy
