# Quickstart

1. Start server:
   - `PYTHONPATH=src python -m media_workbench.main serve --workspace ./workspace --port 8765`
2. Health check:
   - `curl http://127.0.0.1:8765/health`
3. Inspect local engines:
   - `curl http://127.0.0.1:8765/capabilities`
4. Ingest file and enqueue default job:
   - POST `/ingest-and-enqueue` with JSON payload.
5. Or use the helper:
   - `python scripts/dev/api_ingest_wait.py --file /path/to/file.wav --media-kind audio --print-output`
6. Monitor:
   - GET `/jobs`, `/jobs/<id>/logs`, `/status`.
