# Goals and Non-Goals

## Goals
- Deliver a local-first installable app for OCR + ASR workflows.
- Preserve raw assets and write derived artifacts into user-visible folders.
- Provide reliable queueing with bounded concurrency and restart durability.
- Support local-only operation by default.
- Add optional, explicit OpenAI-compatible enrichment connectors.
- Provide manual labeling for recurring face/speaker clusters without identity claims.

## Non-Goals (v1)
- Automatic real-person identification from biometric signals.
- Cloud-hosted mandatory architecture.
- Enterprise-only deployment assumptions.
- Real-time streaming transcription at scale.
- Mobile app clients.
- Hidden telemetry.

## Guardrails
- Privacy notice for any external connector usage.
- No sensitive trait inference features or prompts.
- No opaque storage-only workflows; filesystem remains primary evidence layer.
