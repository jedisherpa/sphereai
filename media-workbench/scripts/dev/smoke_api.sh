#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

WORKSPACE_DIR="${WORKSPACE_DIR:-$ROOT_DIR/workspace}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"
PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi
fi

PYTHONPATH=src "$PYTHON_BIN" -m media_workbench.main serve --workspace "$WORKSPACE_DIR" --host "$HOST" --port "$PORT" >/tmp/media_workbench_server.log 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 20); do
  if curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_health.json 2>/dev/null; then
    break
  fi
  sleep 0.25
done

cat /tmp/media_workbench_health.json
curl -fsS "http://$HOST:$PORT/status" | tee /tmp/media_workbench_status.json

echo "Smoke checks passed."
