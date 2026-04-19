# Definition of Done (Program-Level)

## Functional
- User can ingest screenshots/audio and process locally.
- OCR output includes text, bounding boxes, confidence, and source references.
- Transcript output includes timestamped segments and export formats.
- Search works across OCR/transcript/tag/label/status/date filters.
- Export workflows produce deterministic, documented outputs.

## Reliability
- Queue state survives app restart.
- Failed jobs are retryable; canceled jobs are explicit.
- Concurrency default is bounded to 3-4 and configurable.
- Crash recovery and corruption handling paths are documented and tested.

## Privacy/Safety
- No automatic biometric identity recognition behavior or claims.
- No sensitive-trait inference behavior in prompts/UI.
- External connector use is explicit, opt-in, and logged.

## Packaging/Operations
- Install/run path documented for Windows/macOS/Linux.
- Core app works without optional helper.
- Reproducible build scripts exist.

## Quality Evidence
- Unit/integration/e2e coverage for critical flows.
- Manual QA checklist complete for core user journeys.
- Known issues and limitations documented honestly.
