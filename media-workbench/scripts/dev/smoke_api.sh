#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

WORKSPACE_DIR="${WORKSPACE_DIR:-$ROOT_DIR/workspace}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"

PYTHONPATH=src python -m media_workbench.main serve --workspace "$WORKSPACE_DIR" --host "$HOST" --port "$PORT" >/tmp/media_workbench_server.log 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID >/dev/null 2>&1 || true' EXIT

sleep 1

curl -fsS "http://$HOST:$PORT/health" | tee /tmp/media_workbench_health.json
curl -fsS "http://$HOST:$PORT/status" | tee /tmp/media_workbench_status.json

echo "Smoke checks passed."
