#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

resolve_charles_cli() {
  if [ -n "${CHARLES_CLI_BIN:-}" ] && [ -x "$CHARLES_CLI_BIN" ]; then
    printf '%s\n' "$CHARLES_CLI_BIN"
    return 0
  fi

  if command -v charles-cli >/dev/null 2>&1; then
    command -v charles-cli
    return 0
  fi

  local os arch cand
  os="$(uname -s)"
  arch="$(uname -m)"
  case "${os}/${arch}" in
    Darwin/arm64)  cand="$SKILL_DIR/scripts/charles-cli-darwin-arm64" ;;
    Darwin/x86_64) cand="$SKILL_DIR/scripts/charles-cli-darwin-x86_64" ;;
    Linux/x86_64)  cand="$SKILL_DIR/scripts/charles-cli-linux-x86_64" ;;
    *) return 1 ;;
  esac

  [ -x "$cand" ] || return 1
  printf '%s\n' "$cand"
}

status_json() {
  local bin="$1"
  "$bin" status -f json 2>/dev/null || printf '{}\n'
}

json_has_true() {
  local json="$1" key="$2"
  printf '%s\n' "$json" | grep -Eq "\"${key}\"[[:space:]]*:[[:space:]]*true"
}

json_status_running() {
  local json="$1"
  printf '%s\n' "$json" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"running"'
}

is_ready() {
  local json="$1"
  json_status_running "$json" \
    && json_has_true "$json" "proxy_port_open" \
    && json_has_true "$json" "web_interface_enabled"
}

ensure_running() {
  local bin="$1"
  local json
  json="$(status_json "$bin")"
  if is_ready "$json"; then
    return 0
  fi

  # Setup only when control plane/cert is missing.
  if ! json_has_true "$json" "cert_trusted" || ! json_has_true "$json" "web_interface_enabled"; then
    "$bin" setup --trust-cert --yes >/dev/null
  fi

  "$bin" start >/dev/null || true

  local i
  for i in $(seq 1 15); do
    json="$(status_json "$bin")"
    if is_ready "$json"; then
      return 0
    fi
    sleep 1
  done

  echo "charles-fast: Charles is not ready after start/setup" >&2
  echo "$json" >&2
  return 1
}

usage() {
  cat <<'EOF'
Usage: charles-fast.sh <command> [args...]

Commands:
  bin                             Print resolved charles-cli binary path
  status                          Print status JSON
  setup                           Run setup --trust-cert --yes
  ensure                          Ensure Charles is running and controllable
  clear                           Clear current session
  record-start                    Start recording
  record-stop                     Stop recording
  export <path> [format]          Export session (default format: json)
  stop                            Stop Charles
EOF
}

main() {
  local cmd="${1:-}"
  if [ -z "$cmd" ]; then
    usage
    exit 1
  fi
  shift || true

  local bin
  bin="$(resolve_charles_cli)" || {
    echo "charles-fast: unable to resolve charles-cli binary" >&2
    exit 1
  }

  case "$cmd" in
    bin)
      printf '%s\n' "$bin"
      ;;
    status)
      "$bin" status -f json
      ;;
    setup)
      "$bin" setup --trust-cert --yes
      ;;
    ensure)
      ensure_running "$bin"
      "$bin" status -f json
      ;;
    clear)
      ensure_running "$bin"
      "$bin" session clear
      ;;
    record-start)
      ensure_running "$bin"
      "$bin" record start
      ;;
    record-stop)
      "$bin" record stop
      ;;
    export)
      local out="${1:-}"
      local fmt="${2:-json}"
      if [ -z "$out" ]; then
        echo "charles-fast: export requires output path" >&2
        exit 1
      fi
      ensure_running "$bin"
      "$bin" session export "$out" --export-format "$fmt"
      ;;
    stop)
      "$bin" stop || true
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"

