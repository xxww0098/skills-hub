# Linux drive evidence (2026-08-30, cua-driver 0.22.2, XFCE DISPLAY=:1)

Screenshots after a click/type that changed visible UI.

| File | Host | What changed |
|------|------|----------------|
| `gtk-calc-42.png` | GTK3 | AX 6 × 7 → Result 42, `result=42` |
| `gtk-type-ada.png` | GTK3 | `type_text` Ada + Submit → `hello Ada` |
| `electron-before.png` | Electron | AX tree was one frame; CDP refused |
| `electron-calc-42.png` | Electron | Foreground PX → Result 42 |
| `tauri-ax-calc-42.png` | Tauri 2 binary | Background AX → Result 42 |
| `tauri-paint-surface.png` | Tauri 2 | Flutter tab → one `Probe Canvas` |
| `tauri-paint-calc-42.png` | Tauri 2 | Foreground PX on canvas → `result=42` |
| `qt-calc-42.png` | Qt5 Widgets | Background AX → Result 42 |
| `webkitgtk-calc-42.png` | WebKitGTK 4.1 | Background AX → Result 42 |

Re-run: `../linux-smoke.sh`.
