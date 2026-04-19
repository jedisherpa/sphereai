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
