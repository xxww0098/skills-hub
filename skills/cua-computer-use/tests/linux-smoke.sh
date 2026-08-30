#!/usr/bin/env bash
# Repeatable Linux Cua Lab smoke. GTK is required; other hosts are skipped if missing.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CUA="${CUA:-$SKILL_DIR/scripts/cua-use}"
export DISPLAY="${DISPLAY:-:1}"
export PATH="${HOME}/.local/bin:${PATH}"
DRIVE="$SKILL_DIR/tests/linux-lab-drive.py"
LAB="$SKILL_DIR/scripts/linux-lab"
OUT_ROOT="${CUA_LAB_OUT:-/tmp/cua-linux-smoke}"
rm -rf "$OUT_ROOT"
mkdir -p "$OUT_ROOT"

chmod +x "$CUA" "$LAB" "$DRIVE" "$SKILL_DIR/scripts/cua-use"

echo "== ensure + session-bus =="
"$CUA" session-bus
"$CUA" ensure >/dev/null
"$CUA" permissions status --json | tee "$OUT_ROOT/permissions.json"
if ! grep -q '"atspi": true' "$OUT_ROOT/permissions.json"; then
  echo "linux-smoke: atspi is not true after ensure" >&2
  exit 1
fi

# grant must stay a wrapper command, not a raw tool
if "$CUA" grant >/tmp/cua-grant.err 2>&1; then
  echo "linux-smoke: grant unexpectedly succeeded on Linux" >&2
  exit 1
fi
grep -q 'macOS-only' /tmp/cua-grant.err

pids=()
cleanup() {
  local p
  for p in "${pids[@]:-}"; do
    kill "$p" 2>/dev/null || true
  done
}
trap cleanup EXIT

launch() {
  local host="$1"
  "$LAB" "$host" >/tmp/cua-lab-"$host".log 2>&1 &
  pids+=("$!")
}

fail=0
run_host() {
  local host="$1" title="$2"
  shift 2
  local out="$OUT_ROOT/$host"
  echo "== drive $host ($title) =="
  if python3 "$DRIVE" --title "$title" --out "$out" --do-calc "$@"; then
    echo "linux-smoke: $host OK"
  else
    echo "linux-smoke: $host FAILED" >&2
    fail=1
  fi
}

echo "== GTK =="
launch gtk
run_host gtk "Cua Lab GTK"

if python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
  echo "== Qt =="
  launch qt
  run_host qt "Cua Lab Qt"
else
  echo "== Qt SKIP (PyQt5 missing) =="
fi

if python3 -c "import gi; gi.require_version('WebKit2','4.1'); from gi.repository import WebKit2" 2>/dev/null; then
  echo "== WebKitGTK =="
  launch webkit
  run_host webkit "Cua Lab WebKit" --try-cdp
else
  echo "== WebKitGTK SKIP =="
fi

if [ -x "$SKILL_DIR/fixtures/cua-lab/electron/node_modules/.bin/electron" ]; then
  echo "== Electron =="
  launch electron
  run_host electron "Cua Lab" --app-name cua-lab-electron --try-cdp --foreground
else
  echo "== Electron SKIP (npm install electron in fixtures/cua-lab/electron) =="
fi

if [ -x "$SKILL_DIR/fixtures/cua-lab/tauri/src-tauri/target/release/cua-lab" ]; then
  echo "== Tauri =="
  launch tauri
  run_host tauri "Cua Lab" --app-name Cua-lab --try-cdp
else
  echo "== Tauri SKIP (cargo build --release in fixtures/cua-lab/tauri/src-tauri) =="
fi

if ! command -v flutter >/dev/null 2>&1; then
  echo "== Flutter embedder SKIP (no Flutter SDK on this image) =="
fi

echo "== unknown subcommand must not fall through =="
if "$CUA" not-a-real-command >/tmp/cua-unknown.err 2>&1; then
  echo "linux-smoke: unknown command exited 0" >&2
  exit 1
fi
grep -q "unknown command" /tmp/cua-unknown.err

echo "records under $OUT_ROOT"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "linux-smoke: ok"
