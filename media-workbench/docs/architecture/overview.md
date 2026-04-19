# Wave 2 Architecture Overview (Locked for Core Build)

## Process model
- Local app shell (planned Tauri) launches local backend service.
- Backend owns durable queue and orchestration.
- Pipeline workers execute OCR/ASR/diarization tasks and emit deterministic artifacts.
- Optional enrichment connector executes only when explicitly enabled per job.

## Core boundaries
- Filesystem is source-of-truth for raw + derived artifacts.
- SQLite indexes assets/jobs/state and stores audit metadata.
- UI consumes backend APIs only (no direct DB mutation).

## Spike validation status
- Workspace layout creation: validated.
- Durable queue state transitions: validated via local SQLite spike.
- OCR/ASR/diarization file output shape: validated via deterministic spike outputs.
- Connector audit path: validated with `external_compute_used` flag.
