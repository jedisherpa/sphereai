# API Access

Media Workbench runs as a local HTTP API with a background worker. There is no UI requirement for API testing.

## Start the API

```bash
PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765
```

For tokened local API testing, keep the server bound to loopback and pass a bearer token:

```bash
MEDIA_WORKBENCH_API_TOKEN="change-me-local-token" \
PYTHONPATH=src python -m media_workbench.main serve \
  --workspace ./workspace \
  --host 127.0.0.1 \
  --port 8765
```

`GET /health` stays public and reports whether auth is required. All other endpoints require either `Authorization: Bearer <token>` or `X-Media-Workbench-Token: <token>` when a token is configured.

To verify the auth boundary:

```bash
./scripts/dev/smoke_auth.sh
```

## Import a Collection

Import `docs/api/media-workbench.postman_collection.json` into Postman or Insomnia. Set these collection variables:

- `base_url`: `http://127.0.0.1:8765`
- `api_token`: the token used to start the server, or blank for unauthenticated local runs
- `sample_image_path`: path to a local screenshot/image
- `sample_audio_path`: path to a local voice note/audio file

## Inspect Capabilities

```bash
curl -H "Authorization: Bearer change-me-local-token" \
  http://127.0.0.1:8765/capabilities
```

The response reports local OCR/ASR engines, current engine settings, and whether external enrichment is enabled. Local processing is the default. External enrichment requires explicit opt-in through settings/server flags.

## Configure Local Engines

Use Tesseract for OCR when it is installed:

```bash
curl -X POST http://127.0.0.1:8765/settings \
  -H 'Authorization: Bearer change-me-local-token' \
  -H 'Content-Type: application/json' \
  -d '{"ocr_backend":"tesseract","tesseract_path":"tesseract"}'
```

Route ASR to an existing Xenova/Transformers.js Whisper cache:

```bash
curl -X POST http://127.0.0.1:8765/settings \
  -H 'Authorization: Bearer change-me-local-token' \
  -H 'Content-Type: application/json' \
  -d '{
    "asr_backend": "xenova",
    "node_path": "node",
    "xenova_model_root": "/path/to/storage/models",
    "xenova_model": "Xenova/whisper-large",
    "xenova_node_modules": "/path/to/node_modules"
  }'
```

Use a Whisper-compatible CLI instead:

```bash
curl -X POST http://127.0.0.1:8765/settings \
  -H 'Authorization: Bearer change-me-local-token' \
  -H 'Content-Type: application/json' \
  -d '{"asr_backend":"whisper","whisper_path":"whisper"}'
```

## Ingest and Wait

For image OCR:

```bash
python scripts/dev/api_ingest_wait.py \
  --base-url http://127.0.0.1:8765 \
  --api-token change-me-local-token \
  --file /path/to/screenshot.png \
  --media-kind image \
  --print-output
```

For audio ASR:

```bash
python scripts/dev/api_ingest_wait.py \
  --base-url http://127.0.0.1:8765 \
  --api-token change-me-local-token \
  --file /path/to/voice-note.wav \
  --media-kind audio \
  --print-output
```

The client calls `POST /ingest-and-enqueue`, polls `GET /jobs/<id>`, then prints the `GET /export/<asset_hash>` manifest.

## Safety Boundary

Media Workbench does not perform biometric identity recognition. Diarization and clustering outputs are local handles for workflow/testing, not identity claims. External enrichment remains disabled unless explicitly enabled.
