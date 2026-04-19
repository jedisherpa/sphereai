# Program Risks Register (Initial)

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---:|---:|---|---|
| R-01 | Whisper large model runtime/memory too heavy for consumer hardware | High | High | Profile early; provide quantized fallback + configurable model profiles | ASR Lead |
| R-02 | Packaging size too large for smooth install UX | High | High | Compare slim installer vs offline bundle; staged model downloads | Release Lead |
| R-03 | Cross-platform helper permissions (shortcuts, watchers, tray) vary widely | Medium | High | Keep helper optional; graceful degradation path | Desktop Lead |
| R-04 | Queue corruption after crash/restart | Medium | High | Durable state machine + recovery tests + idempotency keys | Backend Lead |
| R-05 | OCR/ASR dependency licensing/redistribution constraints | Medium | High | Licensing audit in Wave 1 with explicit constraints table | Compliance Lead |
| R-06 | User confusion around local vs external enrichment | Medium | High | Explicit UI controls + audit flags + logs | Product + Privacy Lead |
| R-07 | Face/speaker features misinterpreted as identity recognition | Medium | High | Strict copy standards + policy tests + disabled identity claims | Security/Privacy Lead |
| R-08 | Large folder ingest causes memory/IO pressure | Medium | Medium | Backpressure and chunked discovery | Reliability Lead |
