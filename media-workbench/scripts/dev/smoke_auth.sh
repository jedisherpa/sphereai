#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

WORKSPACE_DIR="${WORKSPACE_DIR:-$ROOT_DIR/workspace/auth-smoke}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8769}"
API_TOKEN="${MEDIA_WORKBENCH_API_TOKEN:-local-smoke-token}"
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

MEDIA_WORKBENCH_API_TOKEN="$API_TOKEN" \
PYTHONPATH=src "$PYTHON_BIN" -m media_workbench.main serve --workspace "$WORKSPACE_DIR" --host "$HOST" --port "$PORT" >/tmp/media_workbench_auth_server.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" >/dev/null 2>&1 || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 20); do
  if curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_auth_health.json 2>/dev/null; then
    break
  fi
  sleep 0.25
done

curl -fsS "http://$HOST:$PORT/health" | grep -q '"auth_required": true'

STATUS_CODE="$(curl -sS -o /tmp/media_workbench_auth_unauthorized.json -w '%{http_code}' "http://$HOST:$PORT/status")"
if [ "$STATUS_CODE" != "401" ]; then
  printf 'Expected unauthenticated /status to return 401, got %s\n' "$STATUS_CODE" >&2
  cat /tmp/media_workbench_auth_unauthorized.json >&2
  exit 1
fi

curl -fsS -H "Authorization: Bearer $API_TOKEN" "http://$HOST:$PORT/status" >/tmp/media_workbench_auth_status.json
curl -fsS -H "X-Media-Workbench-Token: $API_TOKEN" "http://$HOST:$PORT/capabilities" >/tmp/media_workbench_auth_capabilities.json

echo "Auth smoke checks passed."
