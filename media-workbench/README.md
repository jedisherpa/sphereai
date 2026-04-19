# Local Media Workbench (Independent Project)

This directory contains a **standalone project** for the local-first media capture/OCR/transcription program.
It does **not** depend on the existing `sphere` CLI package in this repository.

## Current phase
- Wave 1 research artifacts complete.
- Wave 2 verification spikes complete.
- Wave 6 release-prep documentation completed (install matrix + release checklist + known issues).

## Quick checks
```bash
cd media-workbench
PYTHONPATH=src python -m media_workbench.main
```

## Run Wave 3 local service
```bash
cd media-workbench
PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765
```

## API endpoints
- `GET /health`
- `GET /status`
- `POST /ingest` with `{ "source_path": "/path/file.png", "media_kind": "image|audio" }`
- `POST /ingest-and-enqueue` with `{ "source_path": "/path/file.png", "media_kind": "image|audio" }`
- `POST /jobs` with `{ "asset_hash": "...", "job_type": "ocr|asr|diarization|enrichment" }`
- `GET /jobs`
- `GET /jobs/<id>`
- `GET /jobs/<id>/logs`
- `POST /jobs/<id>/cancel`
- `POST /jobs/<id>/retry`
- `GET /search?q=...`
- `GET /export/<asset_hash>`
- `POST /settings` with `{ "max_concurrency": 4, "allow_external_enrichment": false }`

### Safety policy
- No automatic biometric identity recognition.
- Clusters are local-only handles for manual labeling.
- External enrichment stays opt-in and auditable.


## Documentation
- User install: `docs/user/install-guide.md`
- Quickstart: `docs/user/quickstart.md`
- Settings: `docs/user/settings-guide.md`
- Troubleshooting: `docs/user/troubleshooting.md`
- Backup/restore: `docs/user/backup-restore.md`
- Known limitations: `docs/user/known-limitations.md`
- Developer setup: `docs/dev/developer-setup.md`
- Privacy review: `docs/security/privacy-review.md`


## Release preflight
- `PYTHONPATH=src python -m media_workbench.main release-preflight`


## Build/run guide
- See `BUILD_AND_RUN.md` for clone/install/test/run/release-preflight steps.
- Quick smoke script: `./scripts/dev/smoke_api.sh`
- Real OCR smoke script: `./scripts/dev/smoke_ocr.sh`
