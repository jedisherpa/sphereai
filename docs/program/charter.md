# Local-First Media Workbench Program Charter

## Mission
Build an installable local-first application for screenshot/audio ingestion, OCR, transcription, optional enrichment, search, and export, with an optional desktop helper.

## Scope
- Local ingestion for images and audio, including folder imports.
- Durable job queue with retries, cancellation, restart recovery, and configurable concurrency (default 3-4).
- Local OCR with boxes/confidence and local ASR with timestamps (Whisper large baseline).
- Optional speaker diarization and clip extraction.
- Optional face/speaker clustering for recurring-cluster review + manual labels.
- Search and export over user-visible filesystem outputs + SQLite index.
- Optional OpenAI-compatible enrichment connectors with explicit opt-in and external-use audit markers.
- Packaging strategy for Windows/macOS/Linux and optional helper.

## Explicit Safety Boundary
- No automatic biometric identity recognition.
- No public-person matching.
- No sensitive-trait inference.
- Cluster IDs are non-identity handles (e.g., `speaker-cluster-B`).
- User labels are explicit user data only.

## Product Principles
1. Local-first and offline-capable core.
2. Database is index/convenience, not single source of truth.
3. Predictable on-disk layout and deterministic naming.
4. Crash-safe, resumable job processing.
5. Reliability over feature novelty.

## Proposed Platform Targets
- Windows 11/10 (x64)
- macOS 13+ (Apple Silicon + Intel where feasible)
- Linux desktop (Ubuntu LTS baseline, AppImage first)

## Packaging Strategy (Initial)
- Core app: local backend + web UI packaged with Tauri shell.
- Optional helper: separate installable companion process for tray/shortcuts/watched folders.
- Model strategy: slim installer + first-run managed model download with offline bundle option.

## Initial Priorities (P0/P1)
- P0: Ingestion, queue, OCR, transcript, search, export, local-only mode, privacy controls, packaging path.
- P1: Diarization clips, recurring cluster review, optional enrichment connectors, helper UX enhancements.

## Acceptance Criteria (Initial)
- User can import files and get local OCR/transcripts with searchable outputs.
- Jobs persist through restart and can be retried/canceled.
- App remains useful with zero network access.
- External enrichment is clearly opt-in and auditable.
- Installation path documented and testable on target platforms.
