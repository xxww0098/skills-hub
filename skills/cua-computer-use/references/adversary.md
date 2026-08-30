# Adversary notes (live cua-driver 0.22.2)

Caught against a real `cua-driver 0.22.2` binary, not docs memory.
Re-run `cua-use describe <tool>` on the user's version before arguing.

| Trap | What happens | What to do |
|------|----------------|------------|
| `cua-driver grant` | Treated as **tool** `grant`; "no reviewed risk classification"; may exit 0 | `cua-use grant` → `permissions grant`. Never raw `<tool>` |
| `cua-use status` for TCC | `status` is **daemon liveness** | `permissions status --json` |
| `click` with only `element_index` | Stale / rejected without `snapshot_id` | Prefer `element_token` from the same `get_window_state` |
| Reuse index after another snapshot | Explicit stale error | Snapshot again |
| `get_window_state` without `window_id` | Schema requires `pid` **and** `window_id` | Take both from `list_windows` |
| Linux `list_apps` | Every `/proc` pid (bash, tail, driver) | Drive from `list_windows` |
| Linux `list_apps[].active` | Always `false` | Ignore |
| `list_windows` `z_index` null | Stacking unknown | Do not use array order as frontmost |
| Pixel vs AX coords | `elements[].frame` is screen-absolute; click `x,y` is window-local screenshot | Do not copy frame into x,y |
| `call` with daemon down | Exit 1: start `serve` first | `cua-use ensure` |
| Installer `/dev/fd/63` | Some sandboxes; binary may still land in `~/.local/bin` | Wrapper continues if `bin` resolves |
| Telemetry banner | Printed on almost every command | Ignore, or `cua-use telemetry-disable` |
| Typed CDP on Tauri/WebView2 | Structured refusal | AX / PX only |
| Background PX on Unity/Blender | Silent no-op | `bring_to_front` then PX |
| Chromium pixel `right_click` | Becomes left click | AX `right_click` on an element |

Self-check (agent, one shell):

```bash
CUA="<SKILL_DIR>/scripts/cua-use"
chmod +x "$CUA"
"$CUA" bin
"$CUA" doctor --json
"$CUA" ensure
"$CUA" describe click          # must mention element_token / snapshot_id
"$CUA" call list_windows '{"on_screen_only": true}'
```
