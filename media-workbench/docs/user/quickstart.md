# Quickstart

1. Start server:
   - `PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765`
2. Health check:
   - `curl http://127.0.0.1:8765/health`
3. Ingest file:
   - POST `/ingest` with JSON payload.
4. Create processing job:
   - POST `/jobs`.
5. Monitor:
   - GET `/jobs`, `/jobs/<id>/logs`, `/status`.
