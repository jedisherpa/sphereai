#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

WORKSPACE_DIR="${WORKSPACE_DIR:-$ROOT_DIR/workspace/ocr-smoke}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8766}"
PYTHON_BIN="${PYTHON_BIN:-}"
SAMPLE_IMAGE="${SAMPLE_IMAGE:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for OCR smoke checks." >&2
  exit 1
fi

if ! command -v tesseract >/dev/null 2>&1; then
  echo "tesseract is required for real OCR smoke checks. Install it with: brew install tesseract" >&2
  exit 1
fi
TESSERACT_BIN="$(command -v tesseract)"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN="$(command -v python)"
  fi
fi

TMP_DIR=""
if [ -z "$SAMPLE_IMAGE" ]; then
  if ! command -v qlmanage >/dev/null 2>&1; then
    echo "Set SAMPLE_IMAGE=/path/to/image.png when qlmanage is unavailable." >&2
    exit 1
  fi
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/media-workbench-ocr.XXXXXX")"
  TEXT_FILE="$TMP_DIR/ocr_source.txt"
  printf 'INVOICE TOTAL 42\nLOCAL OCR TEST\n' > "$TEXT_FILE"
  qlmanage -t -s 1000 -o "$TMP_DIR" "$TEXT_FILE" >/tmp/media_workbench_qlmanage.log 2>&1
  SAMPLE_IMAGE="$TEXT_FILE.png"
fi

PYTHONPATH=src "$PYTHON_BIN" -m media_workbench.main serve --workspace "$WORKSPACE_DIR" --host "$HOST" --port "$PORT" >/tmp/media_workbench_ocr_server.log 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" 2>/dev/null || true
  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

for _ in $(seq 1 40); do
  if curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_ocr_health.json 2>/dev/null; then
    break
  fi
  sleep 0.25
done

curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_ocr_health.json

jq -n --arg tesseract_path "$TESSERACT_BIN" \
  '{ocr_backend: "tesseract", tesseract_path: $tesseract_path}' |
  curl -fsS -H "Content-Type: application/json" -d @- "http://$HOST:$PORT/settings" >/tmp/media_workbench_ocr_settings.json
CAPABILITIES="$(curl -fsS "http://$HOST:$PORT/capabilities")"
if [ "$(printf '%s' "$CAPABILITIES" | jq -r '.engines.ocr[] | select(.id == "tesseract") | .available')" != "true" ]; then
  printf 'Tesseract is not available according to /capabilities. payload=%s\n' "$CAPABILITIES" >&2
  exit 1
fi

INGEST_JOB="$(
  jq -n --arg source_path "$SAMPLE_IMAGE" '{source_path: $source_path, media_kind: "image"}' |
    curl -fsS -H "Content-Type: application/json" -d @- "http://$HOST:$PORT/ingest-and-enqueue"
)"
ASSET_HASH="$(printf '%s' "$INGEST_JOB" | jq -r '.asset_hash')"
JOB_ID="$(printf '%s' "$INGEST_JOB" | jq -r '.job_id')"

STATE=""
for _ in $(seq 1 40); do
  JOB_PAYLOAD="$(curl -fsS "http://$HOST:$PORT/jobs/$JOB_ID")"
  STATE="$(printf '%s' "$JOB_PAYLOAD" | jq -r '.job.state')"
  [ "$STATE" = "completed" ] && break
  [ "$STATE" = "failed" ] && break
  sleep 0.25
done

LOGS="$(curl -fsS "http://$HOST:$PORT/jobs/$JOB_ID/logs")"
if [ "$STATE" != "completed" ]; then
  printf 'OCR job did not complete. state=%s logs=%s\n' "$STATE" "$LOGS" >&2
  exit 1
fi

if ! printf '%s' "$LOGS" | grep -q "ocr engine: tesseract-cli"; then
  printf 'OCR smoke did not use tesseract-cli. logs=%s\n' "$LOGS" >&2
  exit 1
fi

EXPORT="$(curl -fsS "http://$HOST:$PORT/export/$ASSET_HASH")"
TEXT_PATH="$(printf '%s' "$EXPORT" | jq -r '.manifest.ocr[] | select(endswith("text.txt"))' | head -1)"
if [ -z "$TEXT_PATH" ] || [ ! -f "$TEXT_PATH" ]; then
  printf 'OCR text output was not found. export=%s\n' "$EXPORT" >&2
  exit 1
fi

if ! grep -q "INVOICE TOTAL 42" "$TEXT_PATH"; then
  printf 'OCR text did not contain expected sample text. Output:\n' >&2
  cat "$TEXT_PATH" >&2
  exit 1
fi

printf 'OCR smoke checks passed.\n'
printf 'asset_hash=%s\njob_id=%s\ntext_path=%s\n' "$ASSET_HASH" "$JOB_ID" "$TEXT_PATH"
cat "$TEXT_PATH"
