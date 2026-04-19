#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

WORKSPACE_DIR="${WORKSPACE_DIR:-$ROOT_DIR/workspace/asr-smoke}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8767}"
PYTHON_BIN="${PYTHON_BIN:-}"
SAMPLE_AUDIO="${SAMPLE_AUDIO:-}"

PRISM_MODEL_ROOT="$HOME/Library/Application Support/com.sovereign.prismai.desktop/storage/models"
PRISM_SOURCE_NODE_MODULES="$HOME/Documents/Playground/prism-source/PrismAI/collector/node_modules"
PRISM_APP_NODE_MODULES="$HOME/Applications/PrismAI-Local.app/Contents/Resources/_up_/runtime/core/collector/node_modules"

export MEDIA_WORKBENCH_ASR_BACKEND="${MEDIA_WORKBENCH_ASR_BACKEND:-xenova}"
export MEDIA_WORKBENCH_XENOVA_MODEL_ROOT="${MEDIA_WORKBENCH_XENOVA_MODEL_ROOT:-$PRISM_MODEL_ROOT}"
export MEDIA_WORKBENCH_XENOVA_MODEL="${MEDIA_WORKBENCH_XENOVA_MODEL:-Xenova/whisper-large}"
if [ -z "${MEDIA_WORKBENCH_XENOVA_NODE_MODULES:-}" ]; then
  if [ -d "$PRISM_SOURCE_NODE_MODULES/@xenova/transformers" ]; then
    export MEDIA_WORKBENCH_XENOVA_NODE_MODULES="$PRISM_SOURCE_NODE_MODULES"
  elif [ -d "$PRISM_APP_NODE_MODULES/@xenova/transformers" ]; then
    export MEDIA_WORKBENCH_XENOVA_NODE_MODULES="$PRISM_APP_NODE_MODULES"
  fi
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for ASR smoke checks." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node is required for Xenova ASR smoke checks." >&2
  exit 1
fi
if [ ! -d "$MEDIA_WORKBENCH_XENOVA_MODEL_ROOT/${MEDIA_WORKBENCH_XENOVA_MODEL}" ]; then
  echo "Xenova model not found: $MEDIA_WORKBENCH_XENOVA_MODEL_ROOT/${MEDIA_WORKBENCH_XENOVA_MODEL}" >&2
  exit 1
fi
if [ -z "${MEDIA_WORKBENCH_XENOVA_NODE_MODULES:-}" ] || [ ! -d "$MEDIA_WORKBENCH_XENOVA_NODE_MODULES/@xenova/transformers" ]; then
  echo "Set MEDIA_WORKBENCH_XENOVA_NODE_MODULES to a node_modules directory containing @xenova/transformers." >&2
  exit 1
fi

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
if [ -z "$SAMPLE_AUDIO" ]; then
  if ! command -v say >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Set SAMPLE_AUDIO=/path/to/audio.wav when say or ffmpeg is unavailable." >&2
    exit 1
  fi
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/media-workbench-asr.XXXXXX")"
  say -o "$TMP_DIR/asr_source.aiff" "hello local transcription"
  ffmpeg -y -loglevel error -i "$TMP_DIR/asr_source.aiff" -ar 16000 -ac 1 "$TMP_DIR/asr_source.wav"
  SAMPLE_AUDIO="$TMP_DIR/asr_source.wav"
fi

PYTHONPATH=src "$PYTHON_BIN" -m media_workbench.main serve --workspace "$WORKSPACE_DIR" --host "$HOST" --port "$PORT" >/tmp/media_workbench_asr_server.log 2>&1 &
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
  if curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_asr_health.json 2>/dev/null; then
    break
  fi
  sleep 0.25
done

curl -fsS "http://$HOST:$PORT/health" >/tmp/media_workbench_asr_health.json

INGEST_JOB="$(
  jq -n --arg source_path "$SAMPLE_AUDIO" '{source_path: $source_path, media_kind: "audio"}' |
    curl -fsS -H "Content-Type: application/json" -d @- "http://$HOST:$PORT/ingest-and-enqueue"
)"
ASSET_HASH="$(printf '%s' "$INGEST_JOB" | jq -r '.asset_hash')"
JOB_ID="$(printf '%s' "$INGEST_JOB" | jq -r '.job_id')"

STATE=""
for _ in $(seq 1 240); do
  JOB_PAYLOAD="$(curl -fsS "http://$HOST:$PORT/jobs/$JOB_ID")"
  STATE="$(printf '%s' "$JOB_PAYLOAD" | jq -r '.job.state')"
  [ "$STATE" = "completed" ] && break
  [ "$STATE" = "failed" ] && break
  sleep 0.5
done

LOGS="$(curl -fsS "http://$HOST:$PORT/jobs/$JOB_ID/logs")"
if [ "$STATE" != "completed" ]; then
  printf 'ASR job did not complete. state=%s logs=%s\n' "$STATE" "$LOGS" >&2
  exit 1
fi

if ! printf '%s' "$LOGS" | grep -q "asr engine: xenova-transformers"; then
  printf 'ASR smoke did not use xenova-transformers. logs=%s\n' "$LOGS" >&2
  exit 1
fi

EXPORT="$(curl -fsS "http://$HOST:$PORT/export/$ASSET_HASH")"
TEXT_PATH="$(printf '%s' "$EXPORT" | jq -r '.manifest.transcripts[] | select(endswith("transcript.txt"))' | head -1)"
if [ -z "$TEXT_PATH" ] || [ ! -f "$TEXT_PATH" ]; then
  printf 'ASR transcript output was not found. export=%s\n' "$EXPORT" >&2
  exit 1
fi

if [ ! -s "$TEXT_PATH" ]; then
  printf 'ASR transcript output was empty.\n' >&2
  exit 1
fi

printf 'ASR smoke checks passed.\n'
printf 'model=%s\nasset_hash=%s\njob_id=%s\ntext_path=%s\n' "$MEDIA_WORKBENCH_XENOVA_MODEL" "$ASSET_HASH" "$JOB_ID" "$TEXT_PATH"
cat "$TEXT_PATH"
