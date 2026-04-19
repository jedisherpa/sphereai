# Wave 4 Tuning Notes

- Default concurrency remains `4` for balanced laptop behavior.
- SQLite WAL mode enabled for safer concurrent read/write usage.
- Poll interval tuned to 0.3s default to reduce busy looping.
- Processing metrics table introduced for future throughput regression tracking.
