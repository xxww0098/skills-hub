---
name: charles-cli
description: >
  Drive Charles Proxy from the CLI to capture, inspect, export, and throttle
  HTTP/HTTPS traffic. Use when the user mentions Charles, charles-cli, MITM
  proxy, intercept HTTPS, record API traffic, export HAR/JSON/CSV, SSL
  proxying, throttle 3G/4G, or debug requests between a local app and a
  server. Prefer this over ad-hoc curl or mitmproxy when Charles is the proxy.
---

# charles-cli

Turn Charles into a scriptable proxy. Daily path is `scripts/charles-fast.sh`
(resolves the binary, skips redundant setup, polls readiness — no blind `sleep`).

Replace `<SKILL_DIR>` with this SKILL.md's directory.

## Capture local traffic

```bash
FAST="<SKILL_DIR>/scripts/charles-fast.sh"
"$FAST" ensure          # start only if not already healthy
"$FAST" clear
"$FAST" record-start
# run the target app / generate traffic
"$FAST" export ./traffic.json json
"$FAST" record-stop     # optional
"$FAST" stop            # optional
```

One-time machine bootstrap (cert trust / web control missing):

```bash
"<SKILL_DIR>/scripts/charles-fast.sh" setup
```

## Why `ensure` instead of raw `setup` + `start`

`setup --trust-cert --yes` is slow and needs admin. `charles-fast.sh ensure`
only sets up when cert trust or the web interface is missing, then waits until
Charles is actually controllable.

Override the binary with `CHARLES_CLI_BIN` if needed. Resolution order is
already in the wrapper: env → `charles-cli` on PATH → bundled
`scripts/charles-cli-<os>-<arch>`.

## Fast wrapper

| Command | Does |
|---------|------|
| `ensure` | Resolve binary; start Charles only if not ready |
| `setup` | Force `setup --trust-cert --yes` |
| `status` | Status JSON |
| `clear` | Clear session |
| `record-start` / `record-stop` | Recording |
| `export <path> [json\|har\|csv\|charles]` | Export session (default `json`) |
| `stop` | Stop Charles |
| `bin` | Print resolved `charles-cli` path |

Raw CLI (when the wrapper is not enough): `setup`, `start`, `stop`, `status -f json`,
`record start\|stop`, `session clear`, `session export <path> --export-format …`,
`throttle enable --preset 3G\|4G`, `throttle disable`.

## Capture rules (why traffic is missing)

HTTPS apps that use their own CA pool (Go, Node, Python, Rust) must see Charles
**before** they open sockets:

1. Set CA + proxy env vars
2. Start Charles (`ensure`)
3. Start or **restart** the target app

```bash
export SSL_CERT_FILE=~/.charles-cli/ca-bundle.pem          # Go / OpenSSL
export NODE_EXTRA_CA_CERTS=~/.charles-cli/ca-bundle.pem    # Node
export REQUESTS_CA_BUNDLE=~/.charles-cli/ca-bundle.pem     # Python requests
export http_proxy=http://127.0.0.1:8888
export https_proxy=http://127.0.0.1:8888
```

`setup --trust-cert` puts Charles CA in the macOS keychain **and** writes that
combined bundle. Keychain trust alone is not enough for Go/Node/Python.

Works: browser with system/manual proxy; `curl -x http://127.0.0.1:8888`; apps
that honor `http_proxy` + the CA env vars.

Cannot intercept: certificate pinning; apps that ignore the system proxy
(direct TCP); QUIC/HTTP3 (UDP); mTLS; connections opened before Charles started
(restart the app — not pinning).

## Control API (only if you bypass the wrapper)

Charles web control lives on virtual host `http://control.charles/` and is
reachable **only through the proxy**. Direct `127.0.0.1:8888` returns 503.

```bash
curl -x http://127.0.0.1:8888 http://control.charles/recording/start
```

`setup` must write `<remoteControlConfiguration><enabled>true</enabled>`.
Without it, every record/export/stop fails with "Web Interface is disabled".
Edit `charles.config` only while Charles is stopped (it overwrites on quit).

## Troubleshoot

| Symptom | Fix |
|---------|-----|
| 503 / "Malformed request URL" | Call control API via `-x http://127.0.0.1:8888` |
| "Web Interface is disabled" | Re-run `setup` |
| HTTPS stays "Encrypted" | `decryptSSL` + SSL hosts; then restart the app |
| Go/Node SSL handshake fail | `setup --yes`, set `SSL_CERT_FILE`, restart app |
| Port 8888 busy | `charles-cli setup --port 9999` |
| Config ignored | Stop Charles first |
| App worked until Charles | Startup order — env → Charles → restart app |
