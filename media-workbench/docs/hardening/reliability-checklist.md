# Reliability Checklist

- [x] Durable job states persisted in SQLite
- [x] Restart recovery marks `running` jobs as `retrying`
- [x] Cancel and retry endpoints available
- [x] Per-job logs persisted
- [x] Deterministic output paths per asset hash
- [x] Ingest path/media validation guards basic bad input
- [ ] Real model timeout/cancellation behavior
- [ ] Corrupt model cache recovery
