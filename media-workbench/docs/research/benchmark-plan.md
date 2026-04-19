# Wave 1 Benchmark Plan

## Goals
Measure throughput, latency, reliability, and resource usage for OCR/ASR/diarization pipelines on target hardware tiers.

## Hardware tiers
- Tier A: 16GB RAM, CPU-only laptop
- Tier B: 32GB RAM + mid-tier GPU desktop
- Tier C: Apple Silicon laptop

## Metrics
- OCR items/minute and mean latency per image resolution bucket
- ASR realtime factor (RTF), memory peak, and error rate proxy
- Diarization runtime multiplier vs audio duration
- Queue wait time, job completion rate, retry rates
- Cold-start vs warm-start behavior

## Exit thresholds (initial)
- Queue remains responsive at default concurrency 4.
- No unbounded memory growth on 60-minute audio workloads.
- Recovery from forced restart leaves queue in consistent state.
