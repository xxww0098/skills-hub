---
name: real-browser
description: >
  Attach agent-browser to an existing browser session or an already-running
  CDP-enabled Chrome with the user's login state. Do not open cloned profiles or
  launch a new browser.
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)
---

# Real Browser — Session-First Browser Takeover

> Use the browser that already exists before launching anything new.
> `agent-browser` skill = all browser commands. This skill = how to choose the browser/session.
> Success means attached to a live session, not opened from a copied profile.

## Step 0: Load the `agent-browser` Skill

Before running browser commands, load the `agent-browser` skill, then get the
version-matched workflow:

```bash
agent-browser skills get core
```

## Step 1: Reuse the Current Session

Check whether agent-browser already has a session and use it directly:

```bash
agent-browser session list
agent-browser get url
agent-browser snapshot -i
```

If the current page is usable, keep using plain `agent-browser ...` commands.
For a named existing session:

```bash
agent-browser --session <name> get url
agent-browser --session <name> snapshot -i
```

Use `AGENT_BROWSER_SESSION=<name>` when many commands target the same session.

## Step 2: Take Over an Existing CDP Chrome

If Chrome is already running with remote debugging enabled, connect instead of
launching a new browser:

```bash
agent-browser --auto-connect get url
agent-browser --auto-connect snapshot -i
```

If the user's current logged-in Chrome is not CDP-enabled yet, do not use
`--profile`. Ask them to restart or open Chrome with a CDP port, then attach:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
agent-browser --cdp 9222 get url
agent-browser --cdp 9222 snapshot -i
```

Security: a CDP port gives local processes full browser control. Use it only on
trusted machines and close that Chrome when done.

## No Profile Fallback

Do not use `agent-browser --profile`, `AGENT_BROWSER_PROFILE`,
`--session-name`, saved state files, or `scripts/real_browser.sh` for this
skill's default path. Those create, copy, or restore browser state; they do not
attach to the user's current live session.

## Interact via `agent-browser`

Use the same connection flag for every command in that browser context:

```bash
agent-browser snapshot -i                 # current/default session
agent-browser --session work snapshot -i  # named session
agent-browser --auto-connect snapshot -i  # discovered CDP Chrome
agent-browser --cdp 9222 snapshot -i      # known CDP Chrome
```

## Visibility Guard

If commands fail or return unexpected results, the active target may be a
`chrome://` page or the wrong tab. Diagnose and switch:

```bash
agent-browser get url
agent-browser tab list
agent-browser tab <index-or-tabId>
```

## Login State Notes

| Site type | Examples | Login state |
|-----------|----------|-------------|
| Normal sites | X, Reddit, GitHub, 知乎, V2EX | ✅ Preserved |
| High-security (DBSC/Keychain) | Google, Claude, ChatGPT | ⚠️ May log out |

Live browser sessions expose secrets. Do not echo cookies, tokens, or page
content that is not needed for the task.

## Rules

1. Prefer: current session → named session → `--auto-connect` → known `--cdp <port>`.
2. Do not use profile, state, or launch-script fallbacks.
3. Keep the chosen flag (`--session`, `--auto-connect`, or `--cdp`) consistent across commands.
4. `open` → `wait --load networkidle`.
5. `snapshot -i` before interactions; re-snapshot after navigation or DOM changes.
6. Never mix `chrome-devtools` tool with `agent-browser`.

## Troubleshooting

```bash
agent-browser doctor --offline --quick
agent-browser session list
agent-browser --auto-connect get url
lsof -iTCP:9222 -sTCP:LISTEN    # find a known CDP port (macOS / most Linux)
ss -tlnp | grep :9222            # alternative if lsof is unavailable (Linux)
```
