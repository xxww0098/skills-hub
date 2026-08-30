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
`list_apps` is **always false**.

## Load live tools, then classify

```bash
CUA guide
CUA describe click                # note snapshot_id / element_token
CUA frameworks
```

Do not guess schemas. After `list_windows`, classify (see frameworks.md).

| Clue | Channel |
|------|---------|
| Cocoa / WPF / WinUI / GTK widgets / Qt Widgets | AX `element_token` |
| Electron (VS Code, Slack) | CDP if one window/page; else truncated AX |
| Tauri, WKWebView, WebView2, WebKitGTK | AX then PX. Typed CDP **refused** |
| Flutter | Semantics AX then PX |
| Canvas, Unity, Blender, WebGL | Foreground + PX |

## Drive policy

```text
inspect → classify → act → verify
1. list_windows (not list_apps) to pick pid + window_id
2. launch_app only if it is not running
3. get_window_state {pid, window_id, include_screenshot:true}
4. click / type_text / set_value using element_token from THAT snapshot
5. re-snapshot; never reuse a stale element_index
```

Hard rules (0.22.x live binary):

1. `ensure` + `guide` once per session. `call` needs the daemon (`serve`).
2. `get_window_state` **requires** `pid` and `window_id`.
3. Prefer `element_token`. `element_index` **must** include the matching
   `snapshot_id`. Stale snapshot → error; re-run `get_window_state`.
4. Pixel `x,y` are **window-local screenshot** pixels, not `elements[].frame`.
5. Linux: `list_apps` mixes `/proc` (bash, cua-driver, …). Target from
   `list_windows`. `z_index` may be null — do not use array order.
6. `type_text` into Chromium/WebKit/Electron web is `unverifiable`.
7. Do not `browser_prepare` Tauri / WebView2 / Flutter unless bind succeeds.
8. Stay background unless Unity/Blender/WebGL drop PX, or a webview ignores typing.
9. Login / password / payment / corp-intranet: ask first.
10. Do not click the user's frontmost editor. Do not `kill_app` unless asked.
11. Agents: `CUA call <tool> '<json>'`. Never `cua-driver <tool>`.

Cua Lab title **Cua Lab**. Names: `Probe Increment`, `Probe Key 6`,
`Probe Name Field`, `Probe Gain`, `Probe Row Alpha`, `Probe Canvas`,
`Probe Surface Flutter`. AX smoke: 6 × 7 → `Probe Result` `42`.

## Bounded fallback

Only when the binary **explicitly** says `list-tools` is unknown:

```bash
CUA doctor --json
CUA call list_windows '{"on_screen_only": true}'
```

Then `CUA update`. MCP / sandbox / installers: README.
