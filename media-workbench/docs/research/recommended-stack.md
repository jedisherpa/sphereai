# Wave 1 Recommended Stack

## Core stack
- App shell: **Tauri**
- Frontend: **React + TypeScript** (to be implemented in Wave 3)
- Local backend API: **FastAPI**
- Job/state DB: **SQLite + FTS5**
- OCR worker: **PaddleOCR + OpenCV**
- ASR worker: **faster-whisper** (Whisper large baseline policy)
- Diarization: **pyannote.audio** (optional module)
- Media tooling: **ffmpeg**
- Optional enrichment: **OpenAI-compatible connector adapter**

## Why this stack
- Maximizes local-first/offline core capabilities.
- Minimizes install-time operational complexity.
- Leaves room for optional helper and external enrichment without hard dependence.

## Outstanding spikes for Wave 2
1. Prove OCR/ASR/diarization end-to-end on representative hardware.
2. Validate queue recovery semantics across forced restarts.
3. Validate packaging sizes and first-run model management UX.
