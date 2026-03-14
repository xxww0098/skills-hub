---
name: real-browser
description: >
  Launch a real Chrome with the user's login state (cloned profile), exposing CDP
  on port 9851. Default headless. Pass `--headed` only if user explicitly asks to
  see the browser. Requires the `agent-browser` skill for all browser commands.
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)
---

# Real Browser — Login-State CDP Bridge

> **This skill = launch Chrome with login state + CDP port.**
> **`agent-browser` skill = ALL browser commands (click, fill, type, scroll, eval, etc.).**
> You MUST load BOTH skills to operate a browser.

## Step 0: Load the `agent-browser` Skill

Before running ANY browser command, you **MUST** read and load the `agent-browser`
skill. It contains the full command reference with 50+ commands you will need:
click, fill, type, press, scroll, select, hover, check, eval, snapshot, diff,
screenshot, download, upload, auth, sessions, and more.

**Without loading the `agent-browser` skill, you will not know how to interact
with the browser.** This skill only teaches you how to LAUNCH and CONNECT.

## Step 1: Launch Chrome

```bash
scripts/real_browser.sh              # headless (default, recommended)
scripts/real_browser.sh --headed     # visible window — ONLY if user asks to watch
scripts/real_browser.sh --headed 9888  # visible + custom port
```

**Headed vs headless decision:**
- User says nothing about seeing the browser → **headless** (default)
- User says "let me see", "show me", "带界面", "有头模式" → `--headed`

## Step 2: Interact via `agent-browser --cdp 9851`

After launch, prepend `--cdp 9851` to every `agent-browser` command.
This is the **ONLY** difference from standard `agent-browser` usage.
All commands, patterns, and workflows from the `agent-browser` skill apply as-is.

```bash
agent-browser --cdp 9851 open https://x.com
agent-browser --cdp 9851 snapshot -i
agent-browser --cdp 9851 click @e3
```

## Visibility Guard

If commands fail or return unexpected results, the CDP target may be on a
`chrome://` internal page. Diagnose and fix:

```bash
agent-browser --cdp 9851 get url       # what page am I on?
agent-browser --cdp 9851 tab list      # list all tabs
agent-browser --cdp 9851 tab <index>   # switch to the correct tab
```

## Login State Notes

| Site type | Examples | Login state |
|-----------|----------|-------------|
| Normal sites | X, Reddit, GitHub, 知乎, V2EX | ✅ Preserved |
| High-security (DBSC/Keychain) | Google, Claude, ChatGPT | ⚠️ May log out |

## Rules

1. `--cdp 9851` on **EVERY** `agent-browser` command. No exceptions.
2. Load the **`agent-browser` skill** for all available commands.
3. `open` → always `wait --load networkidle` immediately after.
4. `snapshot -i` before any interaction to get fresh refs.
5. Re-snapshot after any page navigation or DOM change.
6. Never mix `chrome-devtools` tool with `agent-browser`.
7. Port is `9851` unless user passed a custom port to the launch script.

## Troubleshooting

```bash
lsof -iTCP:9851 -sTCP:LISTEN    # find process on port
kill <pid>                       # free the port
rm -f /tmp/.real_browser.lock    # remove stale lock
scripts/real_browser.sh          # re-launch fresh
```
