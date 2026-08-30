# Adversary notes (live cua-driver 0.22.2)

Caught against a real `cua-driver 0.22.2` binary, not docs memory.
Re-run `cua-use describe <tool>` on the user's version before arguing.

Linux rows: 2026-08-30 cloud XFCE (`DISPLAY=:1`).
macOS rows: 2026-08-30 xxwwdeMacBook-Pro (26.6.2 arm64, CuaDriver.app).

| Trap | What happens | What to do |
|------|----------------|------------|
| `cua-driver grant` | Treated as **tool** `grant`; "no reviewed risk classification"; may exit 0 | `cua-use grant` → `permissions grant`. Never raw `<tool>` |
| `cua-use status` for TCC | `status` is **daemon liveness** | `permissions status --json` |
| macOS `ensure` / `call list_apps` | Hung ~90s on 2026-08-30 even with CuaDriver.app `serve` already up | Liveness = `status` or `list_windows`. Never block `ensure` on `list_apps` |
| First `get_window_state` chrome-only (macOS Tauri) | Menus + chrome, `elements_complete:false`, no `AXWebArea` / Probe | Incomplete walk, not HTMLContent collapse. Re-walk `max_elements` ≥ 5000 or query `Web`/`Probe` before PX |
| Linux `permissions status` `atspi: false` | Daemon inherited `DBUS_SESSION_BUS_ADDRESS=autolaunch:`. zbus: `unsupported transport 'autolaunch'`. `doctor` can still say AT-SPI reachable | `cua-use session-bus` then `cua-use ensure` (restarts serve). Need `unix:path=…` |
| `get_window_state` `degraded_reason` autolaunch | `elements` empty, screenshot still written | Fix the bus. Do not classify the app as "no AX" yet |
| `click` with only `element_index` | Stale / rejected without `snapshot_id` | Prefer `element_token` from the same `get_window_state` |
| Reuse index after another snapshot | Explicit stale error | Snapshot again |
| `get_window_state` without `window_id` | Schema requires `pid` **and** `window_id` | Take both from `list_windows` |
| `capture_mode` | Deprecated, ignored. Tree + screenshot always (unless `include_screenshot:false`) | Use `screenshot_out_file` for evidence |
| `query:"Probe"` | Drops `Multiply` / `Equals` / `Clear` | Unfiltered snapshot, or query those names |
| AX label ≠ visible text | Linux: Probe Counter/Result/Log often nameless. macOS Tauri 2: AXStaticText **did** carry `42` / `result=42` | Still verify on the screenshot (`click.effect` is unverifiable) |
| `click.effect` / `type_text` `unverifiable` | UI may have changed anyway | Re-screenshot. GTK type can say `delivery_failed` and still insert text |
| Linux `list_apps` | Every `/proc` pid (bash, tail, driver) | Drive from `list_windows` |
| Linux `list_apps[].active` | Always `false` | Ignore |
| `list_windows` `z_index` | Populated on this X11 session; may be null elsewhere | Do not use array order as frontmost |
| Pixel vs AX coords | `elements[].frame` is screen-absolute; click `x,y` is window-local screenshot | Do not copy frame into x,y |
| Electron Linux, no debug port | `browser_prepare` → `browser_requires_setup`. AX = one `frame` | Foreground PX. Optional: relaunch with `--remote-debugging-port` |
| Electron Linux background PX | `background_unavailable` (occluded/unfocused renderer) | Same click with `delivery_mode:"foreground"` |
| Tauri/WebKitGTK Linux canvas PX | Background `global_input` can no-op | Foreground PX; AX still works on `aria-label` widgets |
| Typed CDP on Tauri/WebView2/WebKitGTK | Structured refusal | AX / PX only |
| Background PX on Unity/Blender | Silent no-op | `bring_to_front` then PX |
| Chromium pixel `right_click` | Becomes left click | AX `right_click` on an element |
| `call` with daemon down | Exit 1: start `serve` first | `cua-use ensure` |
| Installer `/dev/fd/63` | Some sandboxes; binary may still land in `~/.local/bin` | Wrapper continues if `bin` resolves |
| Telemetry banner | Printed on almost every command | Ignore, or `cua-use telemetry-disable` |

Self-check (agent, one shell):

```bash
CUA="<SKILL_DIR>/scripts/cua-use"
chmod +x "$CUA"
"$CUA" bin
"$CUA" session-bus          # Linux: must print unix:path=…
"$CUA" doctor --json
"$CUA" ensure
"$CUA" permissions status --json   # Linux: atspi true after ensure
"$CUA" describe click          # must mention element_token / snapshot_id / delivery_mode
"$CUA" call list_windows '{"on_screen_only": true}'
```
