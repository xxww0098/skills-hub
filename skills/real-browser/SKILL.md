---
name: real-browser
description: >
  Attach agent-browser only to an already-running, non-agent-browser Chrome
  process that was started with a fixed CDP port. Never discover by using
  agent-browser's default session, cloned profiles, saved state, or new browser
  launches.
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*), Bash(ps:*), Bash(awk:*), Bash(sed:*), Bash(curl:*), Bash(lsof:*)
---

# Real Browser — Existing Chrome CDP Takeover

> Use an existing Chrome process only.
> `agent-browser` skill = all browser commands. This skill = how to choose the browser/session.
> Success means attached to an old non-agent-browser Chrome PID, not a default agent-browser session.

## Step 0: Load the `agent-browser` Skill

Before running browser commands, load the `agent-browser` skill, then get the
version-matched workflow from the installed CLI. Do this as documentation
lookup only, not as a browser session command.

## Step 1: Find an Existing CDP Chrome

Do not run `agent-browser session list`, `agent-browser get url`,
`agent-browser snapshot`, or `agent-browser --auto-connect` as discovery. Those
can attach to or start agent-browser-managed Chrome processes.

First find a user Chrome process that already has a fixed CDP port:

```bash
ps -axo pid=,command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=[1-9][0-9]*/ && !/agent-browser-chrome-/ && !/--headless/ {print}'
```

Extract the port, ignoring `--remote-debugging-port=0` because that is a
dynamic agent-browser launch:

```bash
PORT="$(ps -axo command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=[1-9][0-9]*/ && !/agent-browser-chrome-/ && !/--headless/ {print; exit}' | sed -nE 's/.*--remote-debugging-port=([1-9][0-9]*).*/\1/p')"
test -n "$PORT"
```

If no port is found, stop. A normal already-running Chrome cannot be converted
into a CDP browser from the outside. Ask the user to restart that same Chrome
with a fixed `--remote-debugging-port` and rerun the skill.

## Step 2: Verify CDP Without Launching

Probe the existing port directly:

```bash
curl -fsS "http://127.0.0.1:${PORT}/json/version" >/dev/null
```

Only after the curl check passes, attach with `--cdp`:

```bash
agent-browser --cdp "$PORT" get url
agent-browser --cdp "$PORT" snapshot -i
```

Security: a CDP port gives local processes full browser control. Use it only on
trusted machines and close that Chrome when done.

## No Profile Fallback

Do not use `agent-browser --profile`, `AGENT_BROWSER_PROFILE`,
`--session-name`, saved state files, or `scripts/real_browser.sh` for this
skill's default path. Those create, copy, or restore browser state; they do not
attach to the user's current live session.

Also do not use `agent-browser` without `--cdp "$PORT"` in this skill. Plain
`agent-browser ...` commands target the default agent-browser session and may
create a new Chrome.

## Interact via `agent-browser`

Use the same connection flag for every command in that browser context:

```bash
agent-browser --cdp "$PORT" snapshot -i
agent-browser --cdp "$PORT" click @e3
```

## Visibility Guard

If commands fail or return unexpected results, the active target may be a
`chrome://` page or the wrong tab. Diagnose and switch:

```bash
agent-browser --cdp "$PORT" get url
agent-browser --cdp "$PORT" tab list
agent-browser --cdp "$PORT" tab <index-or-tabId>
```

## Login State Notes

| Site type | Examples | Login state |
|-----------|----------|-------------|
| Normal sites | X, Reddit, GitHub, 知乎, V2EX | ✅ Preserved |
| High-security (DBSC/Keychain) | Google, Claude, ChatGPT | ⚠️ May log out |

Live browser sessions expose secrets. Do not echo cookies, tokens, or page
content that is not needed for the task.

## Rules

1. First prove an existing non-agent-browser Chrome PID has a fixed CDP port.
2. If no such process exists, stop; do not create one.
3. Do not use profile, state, session, auto-connect, or launch-script fallbacks.
4. Use `--cdp "$PORT"` on every `agent-browser` command.
5. `open` → `wait --load networkidle`.
6. `snapshot -i` before interactions; re-snapshot after navigation or DOM changes.
7. Never mix `chrome-devtools` tool with `agent-browser`.

## Troubleshooting

```bash
ps -axo pid=,command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=/ {print}'
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
curl -fsS "http://127.0.0.1:${PORT}/json/version"
```
