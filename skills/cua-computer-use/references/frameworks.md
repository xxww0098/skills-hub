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
- `type_text` into Chromium/WebKit/Electron web content returns
  `effect: unverifiable`. Prefer CDP `page` on Electron; otherwise px-click
  the field then type, and verify from the screenshot.
- `elements[].frame` is screen-absolute; pixel actions are **window-local
  screenshot pixels**. Prefer `element_index` / `element_token` when AX exists.

## Classify (do this once)

From `list_windows` first (pid + window_id + title). On Linux, **do not**
pick a pid from `list_apps` — that list is `/proc` and includes shells.

Then `get_window_state` with `include_screenshot: true`. Click with
`element_token` from that snapshot (or `element_index` **plus** `snapshot_id`).
If the tree is one `AXWebArea` / `HTMLContent` / `FlutterView` / empty,
**stop using AX for inner controls**.

| Clue | Surface | Channel order |
|------|---------|----------------|
| `*.app` Cocoa / Calculator / System Settings | Native | AX |
| `Electron`, `Code`, Slack, Discord, Figma (desktop) | Electron | CDP → AX (truncate) → PX |
| `tauri`, `productName` from `tauri.conf.json`, `Cua Lab` | Tauri | AX → PX. Never `browser_prepare` unless bind succeeds |
| `flutter` / `runner` / Dart VM in the process | Flutter | Semantics AX → PX (+ foreground if ignored) |
| `Unity`, `Blender`, `*.exe` game, WebGL canvas | Canvas | Foreground + PX |
| `Qt*` / `PyQt` / `QtQuick` | Qt Widgets = AX; Qt Quick = PX | |
| GTK 3/4, GNOME apps | GTK | AT-SPI AX; Wayland keys may need `set_value` or XWayland |
| WPF / WinUI / WinForms | Native UIA | AX first |
| VS Code / Cursor | Electron | CDP if one window/page; else AX |

Electron AX trees are huge — pass `max_elements` / `max_depth` / `query`.

## Widgets (any toolkit)

| Widget | First try | Fallback |
|--------|-----------|----------|
| Button, switch, checkbox | AX name / role + `click` | Screenshot + `x,y` |
| Text field | AX `set_value` or `type_text` | Electron: `page` insert_text. Else px-focus + type. Web AX is unverifiable |
| Slider / spinner | `set_value` | `drag` on the thumb |
| List / table row | AX name of the row | Scroll into view, then PX |
| Menu / context menu | AX `press` / `click` | **Do not** pixel-`right_click` Chromium web — it becomes a left click |
| Tab | AX selected tab | PX on the tab label |
| Canvas, video, WebGL, custom paint | — | PX. Foreground if the click vanishes |
| Window chrome (close, title) | Native AX | PX on chrome only |

Unique accessible names beat coordinates. Fixture (Cua Lab):
`Probe Increment`, `Probe Key 6`, `Probe Name Field`, `Probe Gain`,
`Probe Row Alpha`, `Probe Canvas`, `Probe Surface Flutter`, `Probe Log`.

## Per runtime

### Native (AppKit, UIA, AT-SPI widgets)

Background AX works. Stay off `bring_to_front`. Linux Wayland: `press_key` into
unfocused GTK/Qt may return `background_unavailable` — use `set_value` /
`element_index` click, or `delivery_mode:"foreground"`, or XWayland.

### Electron (VS Code, Slack, desktop Figma)

1. `describe browser_prepare` / `get_browser_state`. If the PID binds to one
   CDP page, use `page` (click_element, insert_text). That is the only
   **typed** web path Cua claims.
2. Else `get_window_state` with `query` and truncated depth. Click with `element_token`.
3. Inner web still unverifiable for `type_text` — verify on screenshot.
4. Multi-window Electron (DevTools + app) is **not** the validated shape.
   Drive the content window with AX/PX; do not guess extra CDP targets.

### Tauri / WKWebView / WebView2 / WebKitGTK

Typed CDP **unsupported** (Cua limits). `browser_prepare` will refuse the
common split-process WebView2 and every Tauri host.

1. Match **window title = productName** (fixture: `Cua Lab`). Ignore Vite PID.
2. Unique `aria-label` may appear on WebView2; WKWebView often collapses to
   one HTMLContent node → PX.
3. `type_text` may need one `bring_to_front`.
4. Only if **you** `launch_app` with `webkit_inspector_port` (schema must list
   it) do you get `WEBKIT_INSPECTOR_SERVER` + `TAURI_WEBVIEW_AUTOMATION`.
   An already-running `tauri dev` usually does not have those env vars.
5. Rust rebuild changes PID. Vite HMR does not.

### Flutter (desktop / embedder)

The engine paints. Semantics feed AX **only if** the widget wrapped
`Semantics` / standard Material controls and the embedder enabled a11y.

1. `get_window_state`. If labels exist, use them.
2. If the tree is `FlutterView` + empty children: **PX**, same as canvas.
3. CustomPainter / games: foreground + PX (same GHOST/Unity filter).
4. Do not use `browser_prepare`. Flutter is not Chromium.

### Qt

- Qt Widgets: treat as native AX.
- Qt Quick / QML: often custom scene graph → PX.
- Wayland: same AT-SPI keyboard limit as GTK.

### Canvas / Unity / Blender / WebGL

`click({pid,x,y})` is dropped unless the window is frontmost. Ask or warn,
then `bring_to_front`, screenshot, click, screenshot. Prefer AX on any
real toolbar around the viewport.

## Cua Lab smoke

Window title `Cua Lab`.

- AX path: `Probe Surface Tauri` (default) → `Probe Key 6` → `Multiply` →
  `7` → `Equals` → `Probe Result` is `42`.
- Paint path: `Probe Surface Flutter` or `Canvas / Game` → keypad becomes
  **one** `Probe Canvas` node. Screenshot and click the drawn 6 × 7 =.
- Also: `Probe Increment`, `Probe Name Field` + `Probe Submit`,
  `Probe Gain`, `Probe Row Alpha`.

```bash
CUA call get_window_state '{"pid":PID,"window_id":WID,"query":"Probe","include_screenshot":true}'
```
