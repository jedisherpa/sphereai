# Known Limitations

- OCR uses a local Tesseract CLI when installed; otherwise it falls back to deterministic spike placeholder logic.
- ASR/diarization processing is still deterministic spike placeholder logic.
- No frontend UI or desktop helper yet.
- Packaging/installers are documented but not implemented.
- Search currently uses simple LIKE strategy, not FTS5 ranking.
