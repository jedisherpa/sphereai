# Data Flow

1. User imports media file.
2. File hashed and copied to date-bucketed `raw/images` or `raw/audio` path.
3. Asset metadata upserted in SQLite.
4. One or more jobs enqueued (`ocr`, `asr`, `diarization`, `enrichment`).
5. Scheduler claims pending jobs up to configured concurrency cap.
6. Workers write derived artifacts to deterministic `derived/*/<asset-hash>/` paths.
7. DB job state and logs updated.
8. Search/export consume filesystem artifacts + DB index.
