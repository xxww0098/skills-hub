---
name: charles-cli
description: >
  Use Charles Proxy as a CLI tool for HTTP/HTTPS traffic debugging.
  Covers: zero-config setup, headless proxy management, traffic recording,
  session export, SSL proxying, and throttling.
  Use when the user wants to inspect, record, or export network traffic
  via Charles Proxy from the command line or AI agent workflow.
---

# charles-cli — AI Agent Skill

Transform Charles Proxy into a scriptable CLI tool. Zero-config setup, headless operation, JSON output.

> **Speed First**: Prefer `scripts/charles-fast.sh` for daily use. It auto-resolves
> the binary, skips unnecessary setup, and waits only until Charles is actually ready.

## When to Use

- Capturing or inspecting HTTP/HTTPS traffic from local apps
- Exporting traffic sessions for analysis (HAR / JSON / CSV)
- Debugging API requests between a client and server
- Simulating slow network conditions (throttling)

## Quick Start — Capture Local App Traffic

```bash
FAST="/Users/xxww/Code/REPO/skills-hub/skills/charles-cli/scripts/charles-fast.sh"

# 1) Ensure Charles is ready (idempotent: skips setup/start when already healthy)
"$FAST" ensure

# 2) Start a clean recording session
"$FAST" clear
"$FAST" record-start

# 3) Run the target app / traffic
# (no fixed sleep required)

# 4) Export captured session
"$FAST" export ./traffic.json json

# 5) Optional stop recording / Charles
"$FAST" record-stop
"$FAST" stop
```

## Fast Path (Minimal Prep Time)

### Daily capture (recommended)

```bash
FAST="/Users/xxww/Code/REPO/skills-hub/skills/charles-cli/scripts/charles-fast.sh"
"$FAST" ensure && "$FAST" clear && "$FAST" record-start
```

### One-time machine bootstrap (only when needed)

Run only if certificate trust / web control is missing:

```bash
"/Users/xxww/Code/REPO/skills-hub/skills/charles-cli/scripts/charles-fast.sh" setup
```

### Why this is faster

- Avoids unconditional `setup --trust-cert --yes` on every run.
- Avoids blind `sleep` delays; uses readiness polling.
- Reuses resolved binary path and skips redundant checks when already running.

## Binary Discovery (Cross-Environment)

Use this resolution order for maximum portability:

1. `command -v charles-cli` (user/system installation)
2. Bundled binaries in this skill:
   - `scripts/charles-cli-darwin-arm64`
   - `scripts/charles-cli-darwin-x86_64`
   - `scripts/charles-cli-linux-x86_64`
   - `scripts/charles-cli-windows-x86_64.exe`
3. Explicit override via env:

```bash
export CHARLES_CLI_BIN="/absolute/path/to/charles-cli-binary"
"$CHARLES_CLI_BIN" status -f json
```

### Reusable Launcher Snippet

```bash
resolve_charles_cli() {
  if [ -n "${CHARLES_CLI_BIN:-}" ] && [ -x "$CHARLES_CLI_BIN" ]; then
    printf '%s\n' "$CHARLES_CLI_BIN"; return 0
  fi
  if command -v charles-cli >/dev/null 2>&1; then
    command -v charles-cli; return 0
  fi

  SKILL_DIR="/Users/xxww/Code/REPO/skills-hub/skills/charles-cli"
  OS="$(uname -s)"; ARCH="$(uname -m)"
  case "${OS}/${ARCH}" in
    Darwin/arm64)  CAND="$SKILL_DIR/scripts/charles-cli-darwin-arm64" ;;
    Darwin/x86_64) CAND="$SKILL_DIR/scripts/charles-cli-darwin-x86_64" ;;
    Linux/x86_64)  CAND="$SKILL_DIR/scripts/charles-cli-linux-x86_64" ;;
    *) return 1 ;;
  esac
  [ -x "$CAND" ] && { printf '%s\n' "$CAND"; return 0; }
  return 1
}

CHARLES_CLI_BIN="$(resolve_charles_cli)" || {
  echo "charles-cli binary not found"; exit 1;
}
```

## Command Reference

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `<bin> setup` | Generate `charles.config` XML, optionally trust root cert | `--trust-cert`, `--port`, `--ssl-hosts`, `--yes`, `--dry-run` |
| `<bin> start` | Start Charles in headless mode with generated config | `--config` |
| `<bin> stop` | Gracefully shut down Charles | |
| `<bin> status` | Show running state, proxy port, web interface, cert trust, CA bundle | `-f json` |
| `<bin> record start` | Begin traffic recording | |
| `<bin> record stop` | Stop traffic recording | |
| `<bin> session clear` | Clear the current session buffer | |
| `<bin> session export <path>` | Export session to file | `--export-format har\|json\|csv\|charles` |
| `<bin> throttle enable` | Activate network throttling | `--preset 3G\|4G\|...` |
| `<bin> throttle disable` | Deactivate throttling | |

### Fast Wrapper Commands (`scripts/charles-fast.sh`)

| Command | Description |
|---------|-------------|
| `ensure` | Resolve binary + ensure Charles is running and controllable |
| `setup` | Force setup (`--trust-cert --yes`) |
| `status` | Print current status JSON |
| `clear` | Clear session |
| `record-start` | Start recording |
| `record-stop` | Stop recording |
| `export <path> [json\|har\|csv\|charles]` | Export current session |
| `stop` | Stop Charles |
| `bin` | Print resolved `charles-cli` binary path |

## What Can Be Captured

### ✅ Works (~80% of scenarios)

| Type | Condition |
|------|-----------|
| Browser traffic | System proxy enabled, or browser manually configured |
| `curl` / `wget` | Pass `-x http://127.0.0.1:8888` |
| Go / Node / Python apps | Set `SSL_CERT_FILE` + `http_proxy` env vars, then restart the app |
| Apps with proxy settings | Configure HTTP proxy in the app's settings |

### ❌ Cannot Be Captured

| Type | Reason | Workaround |
|------|--------|------------|
| Certificate Pinning | App only trusts its own certificate, rejects all CAs | ❌ Requires SSL library hooking (Frida / objection) |
| Apps bypassing system proxy | Direct TCP connection, ignores `http_proxy` | ⚠️ Requires transparent proxy via `iptables`/`pf` |
| QUIC / HTTP3 (UDP) | Charles only proxies TCP | ❌ Requires specialized tools |
| Mutual TLS (mTLS) | Client also has certificate verification | ❌ Requires client certificate |
| Pre-existing long connections | gRPC/WebSocket established before proxy was set | ⚠️ Restart the target app |

### ⚠️ Critical: Startup Order Matters

When capturing HTTPS traffic from apps that use their own CA pool (Go, Node.js, Rust, etc.):

```
1. Set SSL_CERT_FILE env var → pointing to CA bundle
2. Start Charles Proxy        → charles-cli start
3. Start/Restart target app   → the app must connect AFTER proxy is ready
```

**If the target app was started before Charles**, it already has established TLS connections using the original CA pool. Those connections will fail or bypass the proxy. This is NOT certificate pinning — it's a connection lifecycle issue. **Restart the app** to fix it.

> Example: An IDE extension that connects to `*.googleapis.com` on startup will fail
> SSL handshake through Charles if the extension was running before Charles started.
> Solution: Restart the IDE after starting Charles.

## Architecture

### Web Control API

Charles exposes its control API on a **virtual host** `http://control.charles/` accessible **only through the proxy**. Direct requests to `http://127.0.0.1:8888/path` will fail with 503 — they are treated as proxy requests, not control commands.

```bash
# ✅ Correct — through the proxy
curl -x http://127.0.0.1:8888 http://control.charles/recording/start

# ❌ Wrong — bypasses proxy
curl --noproxy '*' http://127.0.0.1:8888/recording/start
```

Available endpoints via `http://control.charles/`:

| Endpoint | Description |
|----------|-------------|
| `/recording/start` | Start recording |
| `/recording/stop` | Stop recording |
| `/session/clear` | Clear session |
| `/session/export-har` | Export as HAR |
| `/session/export-json` | Export as JSON (with full bodies) |
| `/session/export-csv` | Export as CSV |
| `/session/download` | Download Charles native format |
| `/throttling/activate?preset=3G` | Activate throttling |
| `/throttling/deactivate` | Deactivate throttling |
| `/tools/map-remote/enable` | Enable Map Remote |
| `/tools/rewrite/enable` | Enable Rewrite |
| `/quit` | Shut down Charles |

### Config Requirements

The `setup` command generates a `charles.config` XML with these critical sections:

```xml
<?xml version='1.0' encoding='UTF-8' ?>
<?charles serialisation-version='2.0' ?>
<configuration>
  <proxyConfiguration>
    <port>8888</port>
    <decryptSSL>true</decryptSSL>
    <sslLocations>
      <locationPatterns>
        <locationMatch>
          <location>
            <host>*</host>
            <port>443</port>
          </location>
        </locationMatch>
      </locationPatterns>
    </sslLocations>
    <macOSXConfiguration>
      <enableAtStartup>false</enableAtStartup>
    </macOSXConfiguration>
  </proxyConfiguration>
  <toolConfiguration>
    <configs/>
  </toolConfiguration>
  <!-- REQUIRED for Web Control API -->
  <remoteControlConfiguration>
    <enabled>true</enabled>
    <allowAnonymous>true</allowAnonymous>
  </remoteControlConfiguration>
</configuration>
```

> **Critical**: The `<remoteControlConfiguration>` section is **required**. Without it, the Web Control API (`control.charles`) returns "Web Interface is disabled" and all CLI operations (record, export, stop) fail.

### Config File Locations

| Platform | Default Path |
|----------|-------------|
| **macOS** | `~/Library/Preferences/com.xk72.charles.config` |
| **Windows** | `%APPDATA%\Charles\charles.config` |
| **Linux** | `~/.charles.config` |

Rules:
- Only edit when Charles is **not running** — Charles overwrites on shutdown
- Use `charles -config <path>` to load an alternative config
- The `<?charles serialisation-version='2.0' ?>` processing instruction is required

## SSL Certificate Trust

For HTTPS decryption, the Charles Root Certificate must be trusted:

```bash
# Full setup: trust cert + generate CA bundle for Go/Node/Python apps
charles-cli setup --trust-cert --yes
```

This does two things:
1. Adds Charles CA to macOS system keychain (requires admin password)
2. Generates a combined CA bundle at `~/.charles-cli/ca-bundle.pem`

### Intercepting Go / Node.js / Python HTTPS traffic

Apps built with Go, Node.js, or Python often **don't read the macOS keychain**. They use their own CA bundle, so they reject Charles's certificate even after system trust.

**Solution**: Set env vars before starting the target app:

```bash
export SSL_CERT_FILE=~/.charles-cli/ca-bundle.pem       # Go, OpenSSL
export NODE_EXTRA_CA_CERTS=~/.charles-cli/ca-bundle.pem  # Node.js
export REQUESTS_CA_BUNDLE=~/.charles-cli/ca-bundle.pem   # Python requests
export http_proxy=http://127.0.0.1:8888                       # Route traffic through proxy
export https_proxy=http://127.0.0.1:8888                      # Route HTTPS through proxy
```

Then **restart** the target app. The combined bundle includes all system CAs + Charles CA.

> Apps with certificate pinning (hard-coded certificates) cannot be intercepted regardless.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Web API returns 503 "Malformed request URL" | You're calling the API directly. Use proxy: `curl -x http://127.0.0.1:8888 http://control.charles/...` |
| "Web Interface is disabled" | Config missing `<remoteControlConfiguration>`. Re-run `charles-cli setup` |
| HTTPS shows as "Encrypted" | Enable `<decryptSSL>true</decryptSSL>` + add hosts to `<sslLocations>` |
| SSL handshake failed (Go/Node apps) | Run `charles-cli setup --yes`, set `SSL_CERT_FILE=~/.charles-cli/ca-bundle.pem`, restart app |
| Port 8888 in use | Use `--port` flag: `charles-cli setup --port 9999` |
| Config changes ignored | Stop Charles first — it overwrites config on shutdown |
| App worked before but fails after enabling Charles | Startup order issue. Set env vars → start Charles → restart the app |
| Target app connects but traffic not visible | App may bypass `http_proxy`. Check if it's using direct TCP connections |
