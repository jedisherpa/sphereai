# Component Diagram (Textual)

```text
[Tauri Shell/UI]
      |
      v
[Local Backend API] ---- [SQLite app.db]
      |
      +---- [Queue Scheduler]
      |          |
      |          +--> [OCR Worker] -> derived/ocr
      |          +--> [ASR Worker] -> derived/transcripts
      |          +--> [Diarization Worker] -> derived/clips
      |
      +---- [Connector Adapter (optional)] -> derived/enrichment + audit table

[Optional Desktop Helper] -> watched folders, shortcuts, tray, notifications
```
