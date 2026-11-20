#!/usr/bin/env bash
# End-to-end smoke test of the built binary, including code execution.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${1:-$ROOT/release/abramyan-exam-linux-x86_64}"
PORT="${EXAM_PORT:-8099}"
DATA_DIR="$(mktemp -d)"
LOG="$(mktemp)"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.cache/abramyan-exam-venv}"

if [[ ! -x "$BIN" ]]; then
  echo "Build the binary first: bash scripts/build_linux.sh" >&2
  exit 1
fi

EXAM_PORT="$PORT" EXAM_DATA_DIR="$DATA_DIR" EXAM_OPEN_BROWSER=0 "$BIN" >"$LOG" 2>&1 &
PID=$!
cleanup() {
  kill "$PID" 2>/dev/null || true
  rm -rf "$DATA_DIR" "$LOG"
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

EXAM_URL="http://127.0.0.1:$PORT" uv run python "$ROOT/scripts/smoke_api.py"
