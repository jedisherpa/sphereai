# Known Limitations

- OCR uses a local Tesseract CLI when installed; otherwise it falls back to deterministic spike placeholder logic.
- ASR uses a local Whisper-compatible CLI named `whisper`, or an explicitly configured Xenova/Transformers.js Whisper cache, when available; otherwise it falls back to deterministic spike placeholder logic.
- Diarization processing is still deterministic spike placeholder logic.
- No frontend UI or desktop helper yet.
- Packaging/installers are documented but not implemented.
- Search currently uses simple LIKE strategy, not FTS5 ranking.
