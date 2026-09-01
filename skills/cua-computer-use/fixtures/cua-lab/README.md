# Cua Lab fixtures

Real windows for `cua-computer-use`. Not mocked transcripts.

| Host | How to run | Linux channel proven 2026-08-30 |
|------|------------|----------------------------------|
| GTK3 | `python3 gtk/cua-lab-gtk.py` | Background AX |
| Qt5 | `python3 qt/cua-lab-qt.py` | Background AX |
| WebKitGTK 4.1 | `python3 webkit/cua-lab-webkit.py` | Background AX; same surface as Tauri-linux |
| Electron | `cd electron && npm i electron && ./node_modules/.bin/electron . --no-sandbox` | One AX frame; CDP refused; **foreground** PX |
| Tauri 2 | `cd tauri/src-tauri && cargo build --release && ./target/release/cua-lab` | Background AX; paint tab = one `Probe Canvas`; paint PX needs foreground |

Window titles: `Cua Lab` (Electron / Tauri), `Cua Lab GTK`, `Cua Lab Qt`, `Cua Lab WebKit`.

Needs `DISPLAY` (or Wayland) and a `unix:path` session bus. From the skill root:

```bash
CUA=scripts/cua-use
"$CUA" ensure
"$CUA" session-bus
tests/linux-smoke.sh
```

Flutter desktop SDK is **not** bundled. `Probe Surface Flutter` is an HTML canvas stand-in.

`tauri/src-tauri/tauri.conf.json` sets `csp: null`. That is lab-only — do not copy it into a production app.
