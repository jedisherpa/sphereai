#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/dist"
mkdir -p "$OUT_DIR"

BUNDLE="$OUT_DIR/media-workbench-release-docs.tar.gz"

tar -czf "$BUNDLE" \
  -C "$ROOT_DIR" \
  README.md RELEASE_NOTES.md docs/release docs/user docs/dev docs/security

echo "Created release docs bundle: $BUNDLE"
