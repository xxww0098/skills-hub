# Framework playbook (Cua Driver)

Load this when the window is Tauri, Electron, Flutter, Qt, GTK, WPF, canvas, or
another non-Cocoa/Win32 toolkit. Tool names still come from `cua-use guide` /
`describe`. This file is **policy**: which channel to try first.

Cua release limits (do not argue with them):

- Typed browser mutation (CDP `page` / `browser_*`) is **validated** for
  Chrome, Edge, Chromium, and **Electron** (one native window ↔ one CDP page).
- **Safari, Firefox, WebView2, Tauri, WKWebView, WebKitGTK**: typed mutation
  **refused**. Native AX + pixel only.
- Pixel `click({pid,x,y})` on Unity / Blender / many games **no-ops in the
  background**. Foreground first.
- Linux Electron/Chromium PX in the background returns
  `background_unavailable` ("unfocused renderer through X11 background
  injection"). Retry `delivery_mode:"foreground"`. Proven 2026-08-30.
- `type_text` into Chromium/WebKit/Electron web content returns
  `effect: unverifiable`. Prefer CDP `page` on Electron **only if**
  `browser_prepare` bound; otherwise px-click the field then type, and
  verify from the screenshot.
- `elements[].frame` is screen-absolute; pixel actions are **window-local
  screenshot pixels**. Prefer `element_index` / `element_token` when AX exists.
- `click.effect` is often `unverifiable` even when the UI changed. GTK
  `type_text` may add `escalation.reason=delivery_failed` and still type.

## Classify (do this once)

From `list_windows` first (pid + window_id + title + **app_name**). On Linux,
**do not** pick a pid from `list_apps` — that list is `/proc` and includes
shells. Two windows can share title `Cua Lab` (Electron + Tauri); disambiguate
with `app_name` (`cua-lab-electron` vs `Cua-lab`).

Then `get_window_state` (screenshot is on by default; `capture_mode` is
ignored). Click with `element_token` from that snapshot (or `element_index`
**plus** `snapshot_id`). If a **complete** walk is one `frame` /
`HTMLContent` / `FlutterView` / empty, **stop using AX for inner
controls**. A first snapshot that is chrome + Apple menus only
(`elements_complete:false`, no WebArea/Probe) is an **incomplete walk**,
not WKWebView collapse — re-walk with `max_elements` ≥ 5000 (or query
`Web` / `Probe`) before PX. macOS Cua Lab Tauri 2 inner controls live
under **`AXWebArea`**, not `HTMLContent`.

Linux AT-SPI requires a real session bus. If `degraded_reason` contains
`unsupported transport 'autolaunch'`, run `cua-use ensure` (restarts serve
with `unix:path=…`) before classifying "no AX".

| Clue | Surface | Channel order |
|------|---------|----------------|
| `*.app` Cocoa / Calculator / System Settings | Native | AX |
| `Electron`, `Code`, Slack, Discord, Figma (desktop), `cua-lab-electron` | Electron | See Electron § |
| `tauri` / `Cua-lab` / `productName` / WebKitGTK | Tauri-linux | AX (`aria-label`) → foreground PX. Never `browser_prepare` unless bind succeeds |
| `Cua Lab` / `cua-lab` + **`AXWebArea`** (macOS Tauri 2) | Tauri-macOS | Background AX under AXWebArea. Re-walk if the first snapshot has no WebArea. Never `browser_prepare` unless bind succeeds |
| `flutter` / `runner` / Dart VM | Flutter embedder | Semantics AX → PX. **No Flutter SDK here** |
| `Unity`, `Blender`, `*.exe` game, WebGL canvas | Canvas | Foreground + PX |
| `Qt*` / `PyQt` / `Cua Lab Qt` | Qt Widgets = AX; Qt Quick = PX | |
| GTK 3/4, `Cua Lab GTK`, GNOME apps | GTK | AT-SPI AX once the unix:path bus is set |
| WPF / WinUI / WinForms | Native UIA | AX first |
| VS Code / Cursor | Electron | CDP if one window/page **and** an owned endpoint; else AX/PX |

Electron AX trees are huge — pass `max_elements` / `max_depth` / `query`.
`query:"Probe"` drops `Multiply` / `Equals` / `Clear` (those names have no
"Probe"). Snapshot unfiltered for the 6 × 7 path.

## Widgets (any toolkit)

| Widget | First try | Fallback |
|--------|-----------|----------|
| Button, switch, checkbox | AX name / role + `click` | Screenshot + `x,y` |
| Text field | AX `set_value` or `type_text` | Electron: `page` insert_text. Else px-focus + type. Web AX is unverifiable |
| Slider / spinner | `set_value` | `drag` on the thumb |
| List / table row | AX name of the row | Scroll into view, then PX |
| Menu / context menu | AX `press` / `click` | **Do not** pixel-`right_click` Chromium web — it becomes a left click |
| Tab | AX selected tab | PX on the tab label. WebKitGTK `role="tab"` can have **empty** AT-SPI actions — use a real button |
| Canvas, video, WebGL, custom paint | — | PX. Foreground if the click vanishes |
| Window chrome (close, title) | Native AX | PX on chrome only |

Unique accessible names beat coordinates. Fixture (Cua Lab):
`Probe Increment`, `Probe Key 6`, `Probe Name Field`, `Probe Gain`,
`Probe Row Alpha`, `Probe Canvas`, `Probe Surface Flutter`, `Probe Log`.

`Probe Counter` / `Probe Result` / `Probe Log` are often nameless labels
on Linux AT-SPI — the visible `1` / `42` / `result=42` is on the
screenshot. macOS Tauri 2 AXStaticText **did** carry those strings
(2026-08-30); still verify on the screenshot because `click.effect` is
unverifiable.

## Per runtime

### Native (AppKit, UIA, AT-SPI widgets)

Background AX works on Linux GTK3 and Qt5 Widgets after the session bus is
`unix:path`. Stay off `bring_to_front` unless a tool returns
`background_unavailable`. Linux Wayland: `press_key` into unfocused GTK/Qt
may return `background_unavailable` — use `set_value` / `element_index`
click, or `delivery_mode:"foreground"`, or XWayland.

### Electron (VS Code, Slack, desktop Figma)

Linux (proven, cua-driver 0.22.2, stock Electron, no debug port):

1. `get_browser_state` / `browser_prepare` → `browser_requires_setup`
   ("no owned DevTools endpoint"). Do **not** treat CDP as the default.
2. `get_window_state` is one `frame` whose label is the window title.
   Inner `aria-label`s are missing. Do not walk AX for Increment / keypad.
3. Background `click({x,y})` → `background_unavailable`. Retry the **same**
   coordinates with `delivery_mode:"foreground"` (`route: global_input`).
4. Verify on the screenshot. `effect` stays `unverifiable`.

CDP becomes available only if **that** process was launched with
`--remote-debugging-port` (or the skill's `CUA_LAB_CDP_PORT`). Then
`describe browser_prepare` / `get_browser_state` as usual. Multi-window
Electron (DevTools + app) is **not** the validated shape.

macOS Electron CDP → truncated AX → PX was **not** re-proven in this Linux
run.

### Tauri / WKWebView / WebView2 / WebKitGTK

Typed CDP **unsupported**. `browser_prepare` refused on a real Tauri 2
Linux binary and on WebKitGTK (`browser_requires_setup`).

**Linux (proven, Tauri 2 + WebKitGTK 4.1):**

1. Match **window title = productName** (`Cua Lab`) and `app_name` (Vite is
   not the window owner). Ignore leftover Electron windows with the same
   title.
2. `aria-label`s appear as AT-SPI nodes with `press`. Background
   `element_token` click drives Increment and 6 × 7.
3. `Probe Surface Flutter` / Canvas replaces the keypad with one
   `Probe Canvas` node (no inner keys). Screenshot + **foreground** PX
   (background PX reported `global_input` success but did not change the UI).
4. Keep Linux WebKitGTK/AT-SPI wording as-is (`aria-label` + `press`).
   Do not import a macOS `HTMLContent` story onto this surface.

**macOS (proven 2026-08-30, xxwwdeMacBook-Pro, macOS 26.6.2 arm64,
cua-driver 0.22.2 from CuaDriver.app, wry 0.55.1, title `Cua Lab`,
`app_name` `cua-lab`):**

1. Inner `aria-label` Probe nodes sit under **`AXWebArea`** (role name
   AXWebArea, **not** HTMLContent). Background `element_token`
   (`route: accessibility`) completed Increment and 6 × 7 = 42. No PX,
   no `delivery_mode:"foreground"`, no `bring_to_front`.
2. First unfiltered `get_window_state` can look collapsed (window chrome
   + Apple menus, `elements_complete:false`, no WebArea/Probe). That is
   an incomplete walk. Re-walk with `max_elements` ≥ 5000 or query
   `Web` / `Probe` **before** falling back to PX. Missing WebArea ≠
   WKWebView collapse.
3. `browser_prepare` refused:
   `{"refusal":{"code":"browser_requires_setup","message":"no owned endpoint is available; pass allow_launch=true with an isolated profile and verified approval"},"status":"refused"}`.
4. `query:"Probe"` still drops `Multiply` / `Equals`.
5. AXStaticText carried `42` / `result=42` on this drive; still verify
   on the screenshot / Probe Log (`click.effect` is unverifiable).

Do **not** document macOS Tauri 2 / Cua Lab as default “one HTMLContent
node”. That collapse remains a possible WKWebView behavior on **other
apps** / older hosts — unproven for this fixture. WebView2 unique names
and `webkit_inspector_port` / `TAURI_WEBVIEW_AUTOMATION` are still
launch-env only.

Rust rebuild changes PID. Vite HMR does not.

### Flutter (desktop / embedder)

The engine paints. Semantics feed AX **only if** the widget wrapped
`Semantics` / standard Material controls and the embedder enabled a11y.

1. `get_window_state`. If labels exist, use them.
2. If the tree is `FlutterView` + empty children: **PX**, same as canvas.
3. CustomPainter / games: foreground + PX (same GHOST/Unity filter).
4. Do not use `browser_prepare`. Flutter is not Chromium.

This Linux cloud image has **no Flutter SDK**. The Cua Lab
`Probe Surface Flutter` tab is an HTML canvas stand-in, not a Dart
embedder. Do not claim the embedder was driven.

### Qt

- Qt Widgets: treat as native AX (proven on PyQt5: same 6 × 7 path as GTK).
- Qt Quick / QML: often custom scene graph → PX.
- Wayland: same AT-SPI keyboard limit as GTK.

### Canvas / Unity / Blender / WebGL

`click({pid,x,y})` is dropped unless the window is frontmost. Ask or warn,
then `bring_to_front`, screenshot, click, screenshot. Prefer AX on any
real toolbar around the viewport.

## Cua Lab smoke

Window title `Cua Lab` (or `Cua Lab GTK` / `Cua Lab Qt` / `Cua Lab WebKit`).

- AX path: default surface → `Probe Key 6` → `Multiply` → `Probe Key 7` →
  `Equals` → screenshot / `Probe Log` is `result=42`.
- Paint path: `Probe Surface Flutter` or `Canvas / Game` → keypad becomes
  **one** `Probe Canvas` node. Foreground PX on the drawn 6 × 7 =.
- Also: `Probe Increment`, `Probe Name Field` + `Probe Submit`,
  `Probe Gain`, `Probe Row Alpha`.

```bash
CUA call get_window_state '{"pid":PID,"window_id":WID,"screenshot_out_file":"/tmp/lab.png"}'
```

Repeatable Linux hosts: `tests/linux-smoke.sh` (GTK required; Electron /
Tauri / Qt / WebKitGTK when present). macOS Tauri 2 evidence:
`tests/evidence/macos-tauri-*.png` (AXWebArea, background AX).
