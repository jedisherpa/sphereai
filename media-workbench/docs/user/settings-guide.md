# Settings Guide

Settings are persisted in SQLite `settings` table.

Supported keys:
- `max_concurrency` (int)
- `allow_external_enrichment` (bool)
- `ocr_backend` (`auto`, `tesseract`, or `spike`)
- `tesseract_path` (optional path or command name)
- `asr_backend` (`auto`, `xenova`, `whisper`, `whisper-cli`, or `spike`)
- `whisper_path` (optional path or command name for a Whisper-compatible CLI)
- `node_path` (optional path or command name for Node.js)
- `xenova_model_root` (optional local Transformers.js model cache root)
- `xenova_model` (defaults to `Xenova/whisper-small`)
- `xenova_node_modules` (optional local `node_modules` path containing `@xenova/transformers` and `wavefile`)

Update settings:
- POST `/settings` with JSON body.

Inspect active runtime settings and local engine availability:
- GET `/capabilities`.

Example local ASR route:
```bash
curl -X POST http://127.0.0.1:8765/settings \
  -H 'Content-Type: application/json' \
  -d '{
    "asr_backend": "xenova",
    "xenova_model_root": "/path/to/storage/models",
    "xenova_model": "Xenova/whisper-large",
    "xenova_node_modules": "/path/to/node_modules"
  }'
```

Environment variables with the same purpose still work for one-off runs and override persisted backend/model choices. External enrichment remains off unless `allow_external_enrichment` is explicitly enabled.
