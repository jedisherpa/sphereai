# Final Architecture Summary (Current Baseline)

- Standalone local-first Python backend with stdlib HTTP API.
- SQLite-backed durable queue with explicit state machine.
- Filesystem-first storage for raw and derived artifacts.
- Worker engine processes jobs with configurable concurrency (default 4).
- Recovery hook requeues interrupted running jobs on startup.
- Optional external enrichment is explicit and auditable.
