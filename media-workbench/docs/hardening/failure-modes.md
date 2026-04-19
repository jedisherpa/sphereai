# Failure Modes

## Covered
- Process restart during running job -> recovered to `retrying` on next startup.
- Invalid ingest media extension -> HTTP 400 with validation error.
- Unsupported job type -> job transitions to failed/retrying path.

## Not yet fully covered
- Disk full handling.
- Long-running model process termination and partial artifact cleanup.
- File-locking conflicts on shared folders.
