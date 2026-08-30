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

This file is a **discovery stub + policy**, not the tool catalog.
Live tool names come from the `cua-driver` binary. Toolkit routing lives in
[references/frameworks.md](./references/frameworks.md) (also `CUA frameworks`).

Not Anthropic's Computer Use API. Human install: [README.md](./README.md).

## Resolve the CLI once

Pick one executable for the whole session. If it fails, report the exact error
and stop — do not fall through to another binary.

1. `CUA_DRIVER_WRAPPER` if set.
2. Else `<SKILL_DIR>/scripts/cua-use` (macOS/Linux) or `scripts/cua-use.ps1`.
3. Else `CUA_DRIVER_BIN` if executable.
4. Else `cua-driver` on PATH.

`CUA` below is that command.

```bash
CUA="<SKILL_DIR>/scripts/cua-use" && chmod +x "$CUA" && "$CUA" ensure && "$CUA" guide
```

macOS daemon must come from **CuaDriver.app**. Permissions: `CUA grant` then
toggle Accessibility + Screen Recording. Health: `CUA doctor --json`.

## Load live tools, then classify the window

```bash
CUA guide
CUA describe <tool>
CUA frameworks              # toolkit playbook (Tauri / Electron / Flutter / …)
```

Do not guess schemas from this stub. After `list_windows`, **classify** using
[frameworks.md](./references/frameworks.md) before the first inner click.

| Clue | Channel |
|------|---------|
| Cocoa / WPF / WinUI / GTK widgets / Qt Widgets | AX `element_index` |
| Electron (VS Code, Slack) | CDP `browser_prepare`+`page` if one window/page; else truncated AX |
| Tauri, WKWebView, WebView2, WebKitGTK | AX then PX. Typed CDP is **refused** |
| Flutter | Semantics AX then PX |
| Canvas, Unity, Blender, WebGL, custom paint | Foreground + PX |

## Drive policy

```text
inspect → classify → act → verify
1. list_apps / list_windows
2. launch_app only if it is not running
3. get_window_state (AX + screenshot). query / max_elements on huge trees
4. click / type_text / press_key / set_value / drag  — channel from the table
5. screenshot / get_window_state again; stop when the result is visible
```

Rules:

1. `ensure` + `guide` once per session.
2. Prefer AX names over coordinates **except** when the tree is one WebView /
   FlutterView / empty / canvas.
3. Stay in the background unless the playbook says the runtime drops
   background pixels (Unity/Blender/WebGL) or a webview ignores typing.
4. `type_text` into Chromium/WebKit/Electron web is `unverifiable` — verify
   on the screenshot, or use CDP `page` on Electron only.
5. Do not `browser_prepare` a Tauri / WebView2 / Flutter PID unless bind
   actually succeeds.
6. Login / password / payment / corp-intranet: ask first.
7. Do not click the user's frontmost editor. Do not `kill_app` unless asked.
8. Agents use `CUA call <tool>`. Do not invent tools.

Cua Lab fixture (`productName` / title **Cua Lab**): unique names
`Probe Increment`, `Probe Key 6`, `Probe Name Field`, `Probe Gain`,
`Probe Row Alpha`, `Probe Canvas`, `Probe Surface Flutter`.
Smoke AX: 6 × 7 → `Probe Result` `42`. Smoke paint: switch to Flutter/Canvas
and click the drawn keys on `Probe Canvas`.

## Bounded fallback (old cua-driver only)

Only when the binary **explicitly** says `guide` / `list-tools` is unknown:

```bash
CUA doctor --json
CUA call list_apps
CUA call list_windows '{"on_screen_only": true}'
```

Then tell the user to `CUA update`. MCP, sandbox, installers: [README.md](./README.md).
