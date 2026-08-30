---
name: cua-computer-use
description: >-
  Inspect and operate local desktop app windows through Cua Driver CLI:
  accessibility trees, screenshots, and background UI actions that do not
  steal the user's cursor. Use for list apps/windows, get window state, read
  visible UI, click, type, press keys, scroll, drag, set values, launch apps,
  or screenshot. Also use for Electron, Tauri, Flutter, Qt, GTK, WPF, VS Code,
  canvas/WebGL/Unity, Slack, Spotify, Calculator, and other desktop UI.
  Triggers include "computer use", "cua-driver", "electron", "tauri",
  "flutter", "qt", "webview", "canvas", "read Slack", "get app state",
  "后台点窗口", "本机操控", "打开计算器", and "computer-use".
argument-hint: <command> [args...]
---

# Computer Use (Cua Driver)

Stub + policy. Tool schemas come from the **installed** `cua-driver` binary
(`describe` / `guide`). Toolkit routing: [references/frameworks.md](./references/frameworks.md)
or `CUA frameworks`. Live-binary traps: [references/adversary.md](./references/adversary.md).

Not Anthropic's Computer Use API. Install notes: [README.md](./README.md).

## Resolve the CLI once

If it fails, report the exact error and stop. Do not fall through.

1. `<SKILL_DIR>/scripts/cua-use` (macOS/Linux) or `scripts/cua-use.ps1`.
2. Else `CUA_DRIVER_BIN` if executable.
3. Else `cua-driver` on PATH.

`CUA` is that wrapper. Prefer it over raw `cua-driver` — unknown raw tokens
are treated as **tool names** (`cua-driver grant` is not `permissions grant`).

```bash
CUA="<SKILL_DIR>/scripts/cua-use" && chmod +x "$CUA" && "$CUA" ensure && "$CUA" guide
```

macOS daemon **must** come from **CuaDriver.app**. Then:

```bash
CUA grant                         # → permissions grant (not `grant`)
CUA permissions status --json     # TCC. `CUA status` is daemon liveness only
```

Health: `CUA doctor --json`. Linux needs `DISPLAY` or Wayland; `active` in
`list_apps` is **always false**. Linux AT-SPI also needs a **unix:path**
session bus — `DBUS_SESSION_BUS_ADDRESS=autolaunch:` makes
`get_window_state` degrade to screenshot-only (`unsupported transport
'autolaunch'`). `CUA ensure` rewrites that; `CUA session-bus` prints it.
`permissions status.atspi` is the daemon's zbus probe, not doctor's
"org.a11y.Bus reachable".

## Load live tools, then classify

```bash
CUA guide
CUA describe click                # note snapshot_id / element_token / delivery_mode
CUA frameworks
```

Do not guess schemas. After `list_windows`, classify (see frameworks.md).

| Clue | Channel |
|------|---------|
| Cocoa / WPF / WinUI / GTK widgets / Qt Widgets | AX `element_token` |
| Electron (VS Code, Slack) | Linux: CDP only if the process already has a DevTools port; else one AX `frame` → **foreground** PX. macOS: CDP → truncated AX → PX |
| Tauri / WebKitGTK (Linux) | AX (`aria-label` press) works in background. Paint/canvas PX needs **foreground**. Typed CDP refused |
| Tauri 2 / WKWebView (macOS) | Background AX `element_token` under **`AXWebArea`** (Cua Lab, 2026-08-30). First snapshot may be chrome-only (`elements_complete:false`) — re-walk `max_elements` ≥ 5000 or query Web/Probe **before** PX. Missing WebArea ≠ HTMLContent collapse |
| Flutter embedder | Semantics AX then PX. **No Flutter SDK in the Linux cloud run** — HTML `Probe Surface Flutter` is a paint stand-in only |
| Canvas, Unity, Blender, WebGL | Foreground + PX |

## Drive policy

```text
inspect → classify → act → verify
1. list_windows (not list_apps) to pick pid + window_id
2. launch_app only if it is not running
3. get_window_state {pid, window_id}  # screenshot is default; capture_mode ignored
4. click / type_text / set_value using element_token from THAT snapshot
5. re-snapshot; never reuse a stale element_index
6. verify from the new screenshot (or Probe Log). click.effect is often unverifiable
```

Hard rules (0.22.x live binary; Linux cloud + macOS Tauri 2 Cua Lab where noted):

1. `ensure` + `guide` once per session. `call` needs the daemon (`serve`).
   `ensure` liveness is `status` / `list_windows` — do **not** block on
   `list_apps` (macOS hung ~90s with CuaDriver.app already serving).
2. `get_window_state` **requires** `pid` and `window_id`. Prefer
   `screenshot_out_file` over inlining base64.
3. Prefer `element_token`. `element_index` **must** include the matching
   `snapshot_id`. Stale snapshot → error; re-run `get_window_state`.
4. Pixel `x,y` are **window-local screenshot** pixels, not `elements[].frame`.
5. Linux: `list_apps` mixes `/proc` (bash, cua-driver, …). Target from
   `list_windows`. `z_index` is populated on X11 here — still do not use
   array order as frontmost.
6. `type_text` into Chromium/WebKit/Electron web is `unverifiable`. GTK
   `type_text` may report `delivery_failed` and still type — read the
   screenshot.
7. Do not `browser_prepare` Tauri / WebView2 / WebKitGTK / Flutter unless
   bind succeeds. Default Electron on Linux **refuses** CDP
   (`browser_requires_setup`) unless launched with `--remote-debugging-port`.
8. Stay background for GTK / Qt / Tauri-linux AX **and macOS Tauri 2
   AXWebArea**. Escalate to `delivery_mode:"foreground"` when the binary
   returns `background_unavailable` (Linux Electron/Chromium PX) or when
   a canvas PX reports success but the screenshot does not change.
9. Login / password / payment / corp-intranet: ask first.
10. Do not click the user's frontmost editor. Do not `kill_app` unless asked.
11. Agents: `CUA call <tool> '<json>'`. Never `cua-driver <tool>`.

Cua Lab title **Cua Lab** (GTK/Qt fixtures use `Cua Lab GTK` / `Cua Lab Qt`).
Names: `Probe Increment`, `Probe Key 6`, `Probe Name Field`, `Probe Gain`,
`Probe Row Alpha`, `Probe Canvas`, `Probe Surface Flutter`, `Probe Log`.
AX smoke: 6 × 7 → screenshot / `Probe Log` shows `result=42`. Do **not**
`query:"Probe"` for that path — it drops `Multiply` / `Equals`.
Linux AT-SPI labels often omit the visible number. macOS Tauri 2
AXStaticText **did** carry `42` / `result=42` — still verify on the
screenshot because `click.effect` is unverifiable. Repeatable Linux run:
`tests/linux-smoke.sh`. macOS evidence: `tests/evidence/macos-tauri-*.png`.

## Bounded fallback

Only when the binary **explicitly** says `list-tools` is unknown:

```bash
CUA doctor --json
CUA call list_windows '{"on_screen_only": true}'
```

Then `CUA update`. MCP / sandbox / installers: README.
