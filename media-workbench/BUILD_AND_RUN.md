# Build and Run (No UI)

This guide gets the API running locally so you can test before adding UI/installers.

## 1) Clone
```bash
git clone <your-github-repo-url>
cd <repo>/media-workbench
```

## 2) Create venv
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip setuptools wheel
```

## 3) Install package editable
```bash
pip install -e .
```

## 4) Run tests
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## 5) Start API server
```bash
PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765
```

## 6) Smoke test API
In another terminal:
```bash
./scripts/dev/smoke_api.sh
```

Check local engine availability:
```bash
curl http://127.0.0.1:8765/capabilities
```

## 6a) Smoke test real OCR
After installing Tesseract:
```bash
./scripts/dev/smoke_ocr.sh
```

## 6b) Smoke test local ASR
When a Xenova/Transformers.js Whisper cache is available:
```bash
MEDIA_WORKBENCH_XENOVA_MODEL_ROOT="/path/to/storage/models" \
MEDIA_WORKBENCH_XENOVA_MODEL="Xenova/whisper-large" \
MEDIA_WORKBENCH_XENOVA_NODE_MODULES="/path/to/node_modules" \
./scripts/dev/smoke_asr.sh
```

Persist a local Xenova/Transformers.js Whisper route for normal API runs:
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

Ingest a file and wait for the processing result:
```bash
python scripts/dev/api_ingest_wait.py \
  --base-url http://127.0.0.1:8765 \
  --file /path/to/audio.wav \
  --media-kind audio \
  --print-output
```

## 7) Release preflight
```bash
PYTHONPATH=src python -m media_workbench.main release-preflight
cat docs/release/preflight-report.json
```

## 8) Build release docs bundle
```bash
./scripts/package/build_release_bundle.sh
```

## Push to GitHub
From repo root:
```bash
git remote -v
git push -u origin <branch-name>
```

## GitHub publishing checklist

Use this when you want to publish this project branch to GitHub with traceable verification notes:

```bash
# from repo root
git status
git add media-workbench README.md docs reports
git commit -m "Document media-workbench publishing and usage"

# set remote once (example)
git remote add origin https://github.com/<owner>/<repo>.git

# push branch
git push -u origin <branch-name>
```

Suggested PR body sections:
1. Motivation
2. Functional changes
3. Documentation updates
4. Verification commands + outcomes

Always include exact commands you ran (tests, compile checks, smoke checks) in the PR description.
