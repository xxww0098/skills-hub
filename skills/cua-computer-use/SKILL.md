---
name: cua-computer-use
description: >-
  Inspect and operate local desktop app windows through Cua Driver CLI:
  accessibility trees, screenshots, and background UI actions that do not
  steal the user's cursor. Use for list apps/windows, get window state, read
  visible UI, click, type, press keys, scroll, drag, set values, launch apps,
  or screenshot. Also use for browser windows, webviews, Slack, Spotify,
  Calculator, and other desktop UI. Triggers include "computer use",
  "cua-driver", "cua computer", "read Slack", "read Spotify", "get app state",
  "后台点窗口", "本机操控", "打开计算器", and "computer-use".
argument-hint: <command> [args...]
---

# Computer Use (Cua Driver)

This file is a **discovery stub + policy**, not the tool catalog.
Live tool names, flags, and JSON schemas come from the `cua-driver` binary
that will actually run — so this file cannot drift from the installed version.

Not Anthropic's Computer Use API. Human install / App-vs-CLI notes: [README.md](./README.md).

## Resolve the CLI once

Pick one executable for the whole session. Substitute it before running;
do not fall through to another binary if it fails — report the exact error and stop.

1. `CUA_DRIVER_WRAPPER` if set (this skill's wrapper).
2. Else `<SKILL_DIR>/scripts/cua-use` (macOS/Linux) or `scripts/cua-use.ps1` (Windows).
   `chmod +x` the wrapper if needed.
3. Else `CUA_DRIVER_BIN` if it is executable.
4. Else `cua-driver` on PATH.

Below, `CUA` is a placeholder for that resolved command.

One shell call. Ready the daemon, then load the live guide:

```bash
CUA="<SKILL_DIR>/scripts/cua-use" && chmod +x "$CUA" && "$CUA" ensure && "$CUA" guide
```

Windows: `& <SKILL_DIR>\scripts\cua-use.ps1 ensure; & ... guide`

`ensure` installs cua-driver if missing, starts the daemon, and probes `list_apps`.
macOS daemon must come from **CuaDriver.app**. If `ensure` fails on permissions:

```bash
CUA grant
# toggle Accessibility + Screen Recording ON for CuaDriver in System Settings
CUA status
CUA ensure
CUA guide
```

Prefer JSON for agent-driven health checks: `CUA doctor --json`.

## Load the live guide before acting

Do **not** guess tool names, flags, or JSON shapes from memory or from this stub.

```bash
CUA guide                 # --version + list-tools (version-matched)
CUA describe <tool>       # full schema for the next call
CUA docs mcp              # dump-docs --type mcp -p  (only if you need the whole surface)
```

Then call the specific tool you just described:

```bash
CUA call <tool> '<json>'
```

`call` requires the daemon (`ensure` first). Prefer `element_index` / AX over raw coordinates.

## Drive policy (this skill owns this; the binary does not)

```text
inspect → act → verify
1. list_apps / list_windows
2. launch_app only if it is not running
3. get_window_state (AX tree + screenshot)
4. click / type_text / press_key / scroll / hotkey / set_value / drag
5. get_window_state again; stop when the result is visible
```

Rules:

1. `ensure` + `guide` once per session before the first `call`.
2. `describe` a tool before first use in the session if the schema is unclear.
3. Stay in the background. Do not `bring_to_front` unless the user asks.
4. Do not click the user's frontmost editor.
5. Login / password / payment / corp-intranet windows: ask first.
6. Do not `kill_app` unless the user explicitly wants the process ended.
7. Do not invent tools. If `list-tools` does not list it, stop.
8. Agents must use `CUA call <tool> …`. Do not rely on unknown-subcommand fallthrough.

## Bounded fallback (old cua-driver only)

Use only when the selected binary **explicitly** says `guide` / `list-tools` /
`dump-docs` is an unknown command. Any other failure is not proof of an old
binary — report it rather than guessing.

```bash
CUA doctor --json
CUA call list_apps
CUA call list_windows '{"on_screen_only": true}'
```

Then tell the user to update (`CUA update`) so `list-tools` / `describe` return.
Beyond these read-oriented calls, ask instead of inventing a surface the binary
may not support.

## Out of scope for this stub

MCP registration, isolated `pip install cua` sandboxes, permission-mode
(`standard` / `bounded` / `unrestricted`), and installer details live in
[README.md](./README.md). Default path is **host CLI**, not sandbox, not MCP.
