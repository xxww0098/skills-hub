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
  and "computer-use".
argument-hint: <command> [args...]
---

# Computer Use (Cua Driver)

Cua Driver CLI discovery stub + drive policy. Not Anthropic's Computer Use API.
Schemas come from the **installed** binary (`guide` / `describe`), not this file.

## Resolve the CLI

If resolve fails, report the exact error and stop. Do not fall through.

1. `<SKILL_DIR>/scripts/cua-use` (macOS/Linux) or `scripts/cua-use.ps1`.
2. Else `CUA_DRIVER_BIN` if executable.
3. Else `cua-driver` on PATH.

`CUA` is that wrapper. Prefer it over raw `cua-driver` — unknown raw tokens
are treated as **tool names** (`cua-driver grant` is not `permissions grant`).

## Session bootstrap

```bash
CUA="<SKILL_DIR>/scripts/cua-use" && chmod +x "$CUA" && "$CUA" ensure && "$CUA" guide
```

- `ensure` liveness is `status` / `list_windows`. Never block on `list_apps`
  (macOS hung ~90s with CuaDriver.app already serving).
- macOS daemon **must** come from **CuaDriver.app**. Then `CUA grant`
  (`permissions grant`, not `grant`) and `CUA permissions status --json` (TCC).
  `CUA status` is daemon liveness only. Health: `CUA doctor --json`.
- Linux needs `DISPLAY` or Wayland; `list_apps.active` is **always false**.
  AT-SPI needs a **unix:path** session bus. `DBUS_SESSION_BUS_ADDRESS=autolaunch:`
  degrades `get_window_state` to screenshot-only (`unsupported transport
  'autolaunch'`). `CUA ensure` rewrites that; `CUA session-bus` prints it.
  `permissions status.atspi` is the daemon zbus probe, not doctor's
  "org.a11y.Bus reachable".

## Classify

```bash
CUA guide
CUA describe click                # snapshot_id / element_token / delivery_mode
CUA frameworks
```

Do not guess schemas. After `list_windows`, classify.
Detail: [references/frameworks.md](./references/frameworks.md).

| Clue | Channel |
|------|---------|
| Cocoa / WPF / WinUI / GTK widgets / Qt Widgets | AX `element_token` |
| Electron (VS Code, Slack) | Linux **default: foreground PX**, not CDP. CDP only if a DevTools port already exists; else one AX `frame` → PX. macOS: CDP → truncated AX → PX |
| Tauri / WebKitGTK (Linux) | Background AX (`aria-label`). Never default `browser_prepare`. Paint/canvas PX needs **foreground**. Typed CDP refused |
| Tauri 2 / WKWebView (macOS) | Background AX under **`AXWebArea`**. First snapshot may be chrome-only (`elements_complete:false`) — re-walk `max_elements` ≥ 5000 or query Web/Probe **before** PX. Missing WebArea ≠ HTMLContent collapse. Never default `browser_prepare` |
| Flutter embedder | Semantics AX then PX. **No Flutter SDK in the Linux cloud run** — HTML `Probe Surface Flutter` is a paint stand-in only |
| Canvas, Unity, Blender, WebGL | Foreground + PX |

## Drive loop

```text
inspect → classify → act → verify
1. list_windows (not list_apps) to pick pid + window_id
2. launch_app only if it is not running
3. get_window_state {pid, window_id}  # screenshot is default; capture_mode ignored
4. click / type_text / set_value using element_token from THAT snapshot
5. re-snapshot; never reuse a stale element_index
6. verify on screenshot / Probe Log — click.effect is often unverifiable
```

Hard rules (0.22.x live binary; Linux cloud + macOS Tauri 2 Cua Lab where noted):

**CLI** — `ensure` + `guide` once. `call` needs the daemon (`serve`).
Agents: `CUA call <tool> '<json>'`. Never `cua-driver <tool>`.

**Target** — `get_window_state` **requires** `pid` and `window_id`. Prefer
`screenshot_out_file` over inlined base64. Prefer `element_token`;
`element_index` **must** include matching `snapshot_id` (stale → re-snapshot).
Pixel `x,y` are **window-local screenshot** pixels, not `elements[].frame`.
Linux `list_apps` mixes `/proc` (bash, cua-driver, …) — target from
`list_windows`. `z_index` is populated on X11 here; still do not treat
array order as frontmost.

**Delivery** — `type_text` into Chromium/WebKit/Electron web is `unverifiable`.
GTK `type_text` may report `delivery_failed` and still type — read the screenshot.
Do not `browser_prepare` Tauri / WebView2 / WebKitGTK / Flutter unless bind
succeeds. Linux Electron **refuses** CDP (`browser_requires_setup`) unless
launched with `--remote-debugging-port`. Stay background for GTK / Qt /
Tauri-linux AX **and macOS Tauri 2 AXWebArea**. Escalate to
`delivery_mode:"foreground"` on `background_unavailable` (Linux
Electron/Chromium PX) or when a canvas PX reports success but the screenshot
does not change.

**Safety** — Login / password / payment / corp-intranet: ask first.
Do not click the user's frontmost editor. Do not `kill_app` unless asked.

## Cua Lab smoke

Title **Cua Lab** (GTK/Qt fixtures: `Cua Lab GTK` / `Cua Lab Qt`).
Names: `Probe Increment`, `Probe Key 6`, `Probe Name Field`, `Probe Gain`,
`Probe Row Alpha`, `Probe Canvas`, `Probe Surface Flutter`, `Probe Log`.
AX path: 6 × 7 → screenshot / `Probe Log` shows `result=42`. Do **not**
`query:"Probe"` — it drops `Multiply` / `Equals`.
Linux AT-SPI labels often omit the visible number. macOS Tauri 2
AXStaticText **did** carry `42` / `result=42` — still verify on the
screenshot (`click.effect` is unverifiable).

## Bounded fallback

Only when the binary **explicitly** says `list-tools` is unknown:

```bash
CUA doctor --json
CUA call list_windows '{"on_screen_only": true}'
```

Then `CUA update`. Install / MCP / sandbox: [README.md](./README.md).
Live-binary traps: [references/adversary.md](./references/adversary.md).
Linux smoke: [tests/linux-smoke.sh](./tests/linux-smoke.sh)
(needs `DISPLAY` + `cua-driver`; not GitHub-hosted `ubuntu-latest`).
macOS Tauri 2 AXWebArea notes: [references/frameworks.md](./references/frameworks.md).
