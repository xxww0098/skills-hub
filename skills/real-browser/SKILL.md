---
name: real-browser
description: >
  Attach agent-browser only to an already-running, non-agent-browser Chrome
  that was started with a fixed CDP port. Use when the user wants the live
  Chrome session, existing cookies/login, CDP takeover, agent-browser --cdp,
  or says do not launch a new browser and do not clone a profile. Never use
  agent-browser's default session, --profile, saved state, or
  scripts/real_browser.sh for this path.
---

# Real Browser — existing Chrome CDP takeover

`agent-browser` issues the clicks. This skill chooses **which** browser:
an old user Chrome PID with a fixed CDP port — not a default agent-browser
session.

Load the `agent-browser` skill for command syntax (docs only, no session).

## 1. Find an existing CDP Chrome

Do **not** discover with `agent-browser session list`, `get url`, `snapshot`,
or `--auto-connect`. Those attach to or start managed Chrome.

```bash
ps -axo pid=,command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=[1-9][0-9]*/ && !/agent-browser-chrome-/ && !/--headless/ {print}'

PORT="$(ps -axo command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=[1-9][0-9]*/ && !/agent-browser-chrome-/ && !/--headless/ {print; exit}' | sed -nE 's/.*--remote-debugging-port=([1-9][0-9]*).*/\1/p')"
test -n "$PORT"
```

`--remote-debugging-port=0` is a dynamic agent-browser launch — ignore it.

If no port: stop. You cannot flip a normal Chrome into CDP from the outside.
Ask the user to restart **that same** Chrome with a fixed
`--remote-debugging-port` and rerun.

## 2. Verify, then attach

```bash
curl -fsS "http://127.0.0.1:${PORT}/json/version" >/dev/null
agent-browser --cdp "$PORT" get url
agent-browser --cdp "$PORT" snapshot -i
```

A CDP port is full browser control. Trusted machines only; close Chrome when done.

## Do not fall back to a new browser

`agent-browser --profile`, `AGENT_BROWSER_PROFILE`, `--session-name`, saved
state, and `scripts/real_browser.sh` clone or launch. They are out of scope.

Every command in this session must include `--cdp "$PORT"`. Bare
`agent-browser ...` targets the default session and may spawn Chrome.

```bash
agent-browser --cdp "$PORT" snapshot -i
agent-browser --cdp "$PORT" click @e3
```

Wrong tab / `chrome://` page:

```bash
agent-browser --cdp "$PORT" get url
agent-browser --cdp "$PORT" tab list
agent-browser --cdp "$PORT" tab <index-or-tabId>
```

Normal sites keep login (X, Reddit, GitHub). High-security (Google, Claude,
ChatGPT / DBSC) may drop. Do not echo cookies, tokens, or extra page content.

## Rules

1. Prove an existing non-agent-browser Chrome PID has a fixed CDP port first.
2. No such process → stop; do not create one.
3. No profile / state / session / auto-connect / launch-script fallbacks.
4. `--cdp "$PORT"` on every `agent-browser` command.
5. `open` → `wait --load networkidle`.
6. `snapshot -i` before clicks; re-snapshot after navigation or DOM changes.
7. Never mix `chrome-devtools` tools with `agent-browser`.

```bash
ps -axo pid=,command= | awk '/[G]oogle Chrome/ && /--remote-debugging-port=/ {print}'
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
curl -fsS "http://127.0.0.1:${PORT}/json/version"
```
