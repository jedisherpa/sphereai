# Program Assumptions

## User and Hardware
- Typical users run consumer laptops/desktops with 16-32GB RAM.
- GPU availability is variable; CPU-only path must function.
- Users can tolerate first-run model downloads when clearly communicated.

## Product/Engineering
- A local backend process is acceptable for reliable job orchestration.
- SQLite is sufficient for v1 metadata/indexing with FTS.
- Python workers are acceptable for ML pipelines if isolated behind stable process boundaries.
- Optional helper can be separately packaged and versioned.

## Operational
- Offline core must remain functional even if enrichment connectors are never configured.
- Derived artifacts are durable records and can be regenerated from raw inputs + processor version metadata.
- v1 prioritizes reliability, traceability, and maintainability over maximal feature depth.

## Assumption Risks
- Whisper large local baseline may be too heavy for some target hardware; fallback packaging and runtime profiles required.
- Cross-platform notarization/signing complexity may impact release dates.
