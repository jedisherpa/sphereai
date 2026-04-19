# Wave 4 Benchmarks (Initial)

## Environment
- Local dev sandbox, CPU-only baseline.
- Deterministic spike processors (not full ML models yet).

## Measurements
- Worker loop latency for spike jobs observed in `processing_metrics.duration_ms`.
- Queue status counters available from `/status` endpoint.

## Current results (spike)
- ASR spike job durations: low milliseconds on CPU due placeholder pipeline.
- Throughput constrained mainly by poll interval and SQLite round-trips.

## Important note
These numbers are not representative of real OCR/ASR/diarization model workloads. Real benchmark pass remains pending model integration.
