#!/usr/bin/env bash
# Smoke-test the built Linux binary without opening a browser.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/dist/abramyan-exam"
PORT="${EXAM_PORT:-8099}"
DATA_DIR="$(mktemp -d)"
LOG="$(mktemp)"

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

curl -fsS "http://127.0.0.1:$PORT/health"
echo
curl -fsS "http://127.0.0.1:$PORT/" | grep -q "Начать экзамен"
echo "Smoke test passed"

TOKEN="$(cat "$DATA_DIR/.teacher-token")"
curl -fsS "http://127.0.0.1:$PORT/teacher?token=$TOKEN" >/dev/null
echo "Teacher page passed"
