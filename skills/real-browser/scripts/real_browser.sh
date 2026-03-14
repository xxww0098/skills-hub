#!/bin/sh
# =============================================================================
# real_browser.sh — Launch a CDP-controllable Chrome with user's login state
#
# Does NOT close the user's existing Chrome. Launches a SEPARATE instance
# using a cloned profile directory. Default is HEADLESS (invisible).
#
# Usage:
#   scripts/real_browser.sh [--headed] [PORT]
#
# Examples:
#   scripts/real_browser.sh              # headless on port 9851
#   scripts/real_browser.sh --headed     # visible window on port 9851
#   scripts/real_browser.sh 9888         # headless on port 9888
#   scripts/real_browser.sh --headed 9888
# =============================================================================
set -eu

# ── Parse Arguments ──────────────────────────────────────────────────────────
HEADED=false
PORT=9851

for arg in "$@"; do
  case "$arg" in
    --headed) HEADED=true ;;
    [0-9]*) PORT="$arg" ;;
  esac
done

CDP_URL="http://127.0.0.1:${PORT}"

# ── OS Detection & Paths ─────────────────────────────────────────────────────
OS="$(uname -s 2>/dev/null || echo unknown)"
case "$OS" in
  Darwin*)
    CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    DEFAULT_PROFILE_ROOT="${HOME}/Library/Application Support/Google/Chrome"
    ;;
  Linux*)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      # Windows Subsystem for Linux (WSL)
      WIN_USER_DIR="$(wslpath "$(cmd.exe /c "echo %LOCALAPPDATA%" 2>/dev/null | tr -d '\r')")" 2>/dev/null || \
      WIN_USER_DIR="/mnt/c/Users/$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')/AppData/Local"
      CHROME_BIN="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
      [ ! -f "$CHROME_BIN" ] && CHROME_BIN="/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
      DEFAULT_PROFILE_ROOT="${WIN_USER_DIR}/Google/Chrome/User Data"
    else
      # Native Linux (Ubuntu, Debian, etc)
      CHROME_BIN="google-chrome"
      DEFAULT_PROFILE_ROOT="${HOME}/.config/google-chrome"
      if ! command -v "$CHROME_BIN" >/dev/null 2>&1 && command -v chromium-browser >/dev/null 2>&1; then
        CHROME_BIN="chromium-browser"
        DEFAULT_PROFILE_ROOT="${HOME}/.config/chromium"
      fi
    fi
    ;;
  MINGW*|CYGWIN*|MSYS*)
    # Windows native shells (Git Bash)
    WIN_USER_DIR="$(echo "${LOCALAPPDATA}" | sed 's/\\/\//g')"
    CHROME_BIN="/c/Program Files/Google/Chrome/Application/chrome.exe"
    [ ! -f "$CHROME_BIN" ] && CHROME_BIN="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    DEFAULT_PROFILE_ROOT="${WIN_USER_DIR}/Google/Chrome/User Data"
    ;;
  *)
    warn "Unsupported OS: $OS. Defaulting to Mac paths."
    CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    DEFAULT_PROFILE_ROOT="${HOME}/Library/Application Support/Google/Chrome"
    ;;
esac

CDP_PROFILE_DIR="${HOME}/.chrome-cdp-profile"
AGENT_STATE_DIR="${HOME}/.agent-browser"
LOCK_FILE="/tmp/.real_browser.lock"

CDP_TIMEOUT=160   # 40s max (iterations × 0.25s)

# ── Logging ──────────────────────────────────────────────────────────────────
log()  { printf '\033[0;36m[real_browser]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[real_browser] WARN:\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[0;31m[real_browser] ERROR:\033[0m %s\n' "$*" >&2; cleanup_lock; exit 1; }
ok()   { printf '\033[0;32m[real_browser] ✓\033[0m %s\n' "$*"; }

# ── Lock ─────────────────────────────────────────────────────────────────────
acquire_lock() {
  if [ -f "$LOCK_FILE" ]; then
    lock_pid="$(cat "$LOCK_FILE" 2>/dev/null || true)"
    if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
      fail "Another instance is running (pid=${lock_pid}). Remove ${LOCK_FILE} if stale."
    fi
    warn "Removing stale lock file."
    rm -f "$LOCK_FILE"
  fi
  echo $$ > "$LOCK_FILE"
  trap 'cleanup_lock' EXIT INT TERM
}

cleanup_lock() {
  rm -f "$LOCK_FILE" 2>/dev/null || true
}

# ── Utilities ────────────────────────────────────────────────────────────────
cdp_ready() {
  curl -fsS --connect-timeout 2 "${CDP_URL}/json/version" >/dev/null 2>&1
}

port_free() {
  ! lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1
}

run_cdp() {
  agent-browser --cdp "${PORT}" "$@"
}

cleanup_agent_state() {
  pkill -f 'agent-browser/.*/dist/daemon.js' >/dev/null 2>&1 || true
  pkill -f 'agent-browser.*daemon' >/dev/null 2>&1 || true
  rm -f "${AGENT_STATE_DIR}/default.sock" "${AGENT_STATE_DIR}/default.pid" 2>/dev/null || true
}

# ── Free CDP Port (kill ONLY the old CDP Chrome, not user's Chrome) ──────────
free_cdp_port() {
  pid="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  [ -z "$pid" ] && return 0

  cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  case "$cmd" in
    *--user-data-dir="${CDP_PROFILE_DIR}"*|*--remote-debugging-port=*)
      log "Killing previous CDP Chrome on :${PORT} (pid=${pid})"
      kill "$pid" >/dev/null 2>&1 || true
      sleep 0.5
      if ! port_free; then
        kill -9 "$pid" >/dev/null 2>&1 || true
        sleep 0.3
      fi
      port_free || fail "Cannot free port ${PORT}."
      ;;
    *"Google Chrome"*)
      # This is the user's normal Chrome (no CDP flag) — don't touch it
      fail "Port ${PORT} is used by the user's Chrome. Try a different port: scripts/real_browser.sh 9444"
      ;;
    *)
      fail "Port ${PORT} is occupied by: $(echo "$cmd" | head -c 80) (pid=${pid})."
      ;;
  esac
}

# ── Profile Clone (wipe + recreate every time) ──────────────────────────────
clone_login_state() {
  src="${DEFAULT_PROFILE_ROOT}"
  dst="${CDP_PROFILE_DIR}"

  [ -d "$src" ] || fail "Default Chrome profile not found: ${src}"
  log "Cloning login state → ${dst}"

  # Wipe previous clone completely — always a fresh copy
  rm -rf "${dst}"
  mkdir -p "${dst}/Default"

  # ── Top-level files ──
  for f in "Local State" "First Run"; do
    [ -f "${src}/${f}" ] && cp -f "${src}/${f}" "${dst}/${f}" 2>/dev/null || true
  done

  # ── Critical auth files (SQLite DBs + JSON) ──
  AUTH_FILES="
    Cookies
    Cookies-journal
    Login Data
    Login Data-journal
    Login Data For Account
    Login Data For Account-journal
    Web Data
    Web Data-journal
    Account Web Data
    Account Web Data-journal
    Preferences
    Secure Preferences
    Network Persistent State
    BrowsingTopicsState
    Trust Tokens
    Trust Tokens-journal
    SharedStorage
    SharedStorage-wal
    Extension Cookies
    Extension Cookies-journal
  "

  for f in $AUTH_FILES; do
    [ -f "${src}/Default/${f}" ] && cp -f "${src}/Default/${f}" "${dst}/Default/${f}" 2>/dev/null || true
  done

  # ── Directory-based storage ──
  for d in "Local Storage" "Session Storage" "Extension State" "IndexedDB" \
           "Accounts" "Extensions" "Extension Rules" \
           "databases" "blob_storage" "GCM Store" \
           "Local Extension Settings" "Network" "Sync Data" \
           "Sync App Settings" "Sync Extension Settings"; do
    if [ -d "${src}/Default/${d}" ]; then
      mkdir -p "${dst}/Default/${d}"
      rsync -a \
        --exclude '*.lock' \
        --exclude 'LOCK' \
        "${src}/Default/${d}/" "${dst}/Default/${d}/" 2>/dev/null || true
    fi
  done

  # ── Remove lock/singleton files ──
  find "$dst" -maxdepth 2 \( -name 'SingletonLock' -o -name 'SingletonCookie' -o -name 'SingletonSocket' \) -delete 2>/dev/null || true
  rm -f "${dst}/Default/DevToolsActivePort" 2>/dev/null || true

  ok "Login state cloned."
}

# ── Chrome Launch ────────────────────────────────────────────────────────────
launch_chrome_with_cdp() {
  profile_dir="$1"
  mode_label="headless"
  headless_flag="--headless=new"

  if [ "$HEADED" = "true" ]; then
    mode_label="headed (visible)"
    headless_flag=""
  fi

  log "Launching Chrome [${mode_label}] on CDP :${PORT}..."

  # shellcheck disable=SC2086
  nohup "${CHROME_BIN}" \
    --user-data-dir="${profile_dir}" \
    --remote-debugging-port="${PORT}" \
    ${headless_flag} \
    --no-first-run \
    --no-default-browser-check \
    --disable-hang-monitor \
    --disable-popup-blocking \
    --disable-prompt-on-repost \
    --disable-translate \
    --metrics-recording-only \
    --safebrowsing-disable-auto-update \
    --disable-gpu \
    --window-size=1440,900 \
    about:blank \
    >/dev/null 2>&1 &

  CHROME_PID=$!
  log "  Chrome PID: ${CHROME_PID}"

  sleep 1
  if ! kill -0 "$CHROME_PID" 2>/dev/null; then
    fail "Chrome process exited immediately."
  fi
}

wait_cdp_ready() {
  i=0
  until cdp_ready; do
    i=$((i + 1))
    [ $((i % 16)) -eq 0 ] && log "  Waiting for CDP... ($(( i / 4 ))s)"
    if [ "$i" -ge "$CDP_TIMEOUT" ]; then
      fail "CDP on port ${PORT} did not become ready after $(( CDP_TIMEOUT / 4 ))s."
    fi
    sleep 0.25
  done
  ok "CDP is ready on port ${PORT}."
}

# ── Tab Management ───────────────────────────────────────────────────────────
pin_visible_target() {
  # Try to activate a normal page tab instead of chrome:// internal targets
  idx="$(run_cdp tab list 2>/dev/null | awk '/about:blank|https?:\/\/|chrome:\/\/newtab/ { if (match($0, /\[[0-9]+\]/)) { print substr($0, RSTART+1, RLENGTH-2); exit } }')"
  [ -z "$idx" ] && idx="0"
  run_cdp tab "$idx" >/dev/null 2>&1 || true
}

verify_login_state() {
  profile_dir="$1"
  cookies_file="${profile_dir}/Default/Cookies"
  if [ -f "$cookies_file" ]; then
    size=$(wc -c < "$cookies_file" 2>/dev/null || echo 0)
    if [ "$size" -gt 1024 ]; then
      ok "Cookie database: ${size} bytes — login state available."
      return 0
    fi
  fi
  warn "Cookie database is small or missing."
  return 1
}

# ── Status ───────────────────────────────────────────────────────────────────
print_status() {
  profile_dir="$1"
  if [ "$HEADED" = "true" ]; then
    mode_str="HEADED (visible window)"
  else
    mode_str="HEADLESS (invisible)"
  fi

  log "──────────────────────────────────────────────"
  log "Browser ready! [${mode_str}]"
  log ""
  log "  CDP:     ${CDP_URL}"
  log "  Profile: ${profile_dir}"
  log ""
  log "  Usage:"
  log "    agent-browser --cdp ${PORT} open https://x.com"
  log "    agent-browser --cdp ${PORT} wait --load networkidle"
  log "    agent-browser --cdp ${PORT} screenshot /tmp/page.png"
  log "    agent-browser --cdp ${PORT} snapshot -i"
  log "──────────────────────────────────────────────"
}

# =============================================================================
# ── MAIN ─────────────────────────────────────────────────────────────────────
# =============================================================================

# ── Mode check to prevent reusing the wrong type (headed vs headless) ─────────
skip_reuse=false
current_chrome_pid="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [ -n "$current_chrome_pid" ]; then
  current_cmd="$(ps -p "$current_chrome_pid" -o command= 2>/dev/null || true)"
  case "$current_cmd" in
    *--headless*)
      if [ "$HEADED" = "true" ]; then
        warn "CDP port ${PORT} is currently HEADLESS. We will kill it to launch HEADED mode."
        skip_reuse=true
      fi
      ;;
    *)
      if [ "$HEADED" = "false" ]; then
        warn "CDP port ${PORT} is currently HEADED. We will kill it to launch HEADLESS mode."
        skip_reuse=true
      fi
      ;;
  esac
fi

if [ "$HEADED" = "true" ]; then
  log "Starting... port=${PORT} mode=HEADED"
else
  log "Starting... port=${PORT} mode=HEADLESS"
fi

TARGET_PROFILE="${CDP_PROFILE_DIR}"

acquire_lock
cleanup_agent_state

# ── REUSE if CDP already active AND mode matches ──────────────────────────────
if cdp_ready && [ "$skip_reuse" = "false" ]; then
  ok "CDP already active on port ${PORT} in desired mode — reusing."
  pin_visible_target
  verify_login_state "$TARGET_PROFILE" || true
  print_status "$TARGET_PROFILE"
  exit 0
fi

# ── LAUNCH NEW INSTANCE ──────────────────────────────────────────────────────
free_cdp_port

log "Cloning login state to a separate profile..."
clone_login_state

launch_chrome_with_cdp "$TARGET_PROFILE"
wait_cdp_ready
pin_visible_target
verify_login_state "$TARGET_PROFILE"

print_status "$TARGET_PROFILE"
exit 0
