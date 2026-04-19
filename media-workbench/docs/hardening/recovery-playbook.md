# Recovery Playbook

1. Restart service.
2. On startup, `recover_jobs_on_start()` requeues interrupted jobs (`running` -> `retrying`).
3. Use `/jobs` and `/jobs/<id>/logs` to inspect failed/retrying jobs.
4. Use `/jobs/<id>/retry` to requeue failed/canceled items.
5. Review `processing_metrics` for runtime diagnostics.
