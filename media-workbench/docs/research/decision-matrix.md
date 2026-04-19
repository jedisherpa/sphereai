# Wave 1 Decision Matrix

| Domain | Option A | Option B | Option C | Recommended | Rationale |
|---|---|---|---|---|---|
| OCR | PaddleOCR+OpenCV | Tesseract+OpenCV | Cloud OCR | PaddleOCR+OpenCV | Better modern OCR quality + local-first fit |
| ASR | Whisper ref | faster-whisper | whisper.cpp | faster-whisper | Better local perf/footprint with Whisper family quality |
| Diarization | pyannote.audio | VAD-only | Cloud diarization | pyannote.audio (optional) | Meets clustering needs locally with manual review |
| Runtime shell | Browser-only | Tauri | Electron | Tauri | Better packaging footprint and native integration tradeoff |
| DB/Search | SQLite+FTS5 | DuckDB FTS | Search sidecar | SQLite+FTS5 | Simpler local ops, stable embedded OLTP fit |
| Queue | SQLite durable queue | Redis RQ/Celery | External broker | SQLite durable queue | Zero extra services for non-technical users |
| Enrichment | OpenAI-compatible connector | Provider-specific hardwire | None | Optional connector abstraction | Keeps local-first default while enabling opt-in |
| Packaging | Bundle all models | Slim+download | No installer | Slim+download (+offline bundle) | Balanced UX and size constraints |
