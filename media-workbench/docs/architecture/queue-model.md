# Queue Model

## States
- pending
- running
- completed
- failed
- canceled
- retrying

## Policies
- Global max active jobs defaults to 4.
- Retries bounded by `max_attempts`.
- Failed final attempts become `failed` for dead-letter style review.
- Per-job logs stored in `job_logs`.
