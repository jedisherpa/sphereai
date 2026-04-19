# Wave 1 Research: Queue and Concurrency

## Options considered
1. In-process durable queue backed by SQLite
2. Redis-backed workers (RQ/Celery/Dramatiq)
3. External broker stack

## Evaluation
- **In-process + SQLite** best supports local-first/offline install simplicity.
- **RQ/Celery/Dramatiq** are mature, but introduce broker/runtime dependencies that complicate non-technical installs.

## Recommendation
Adopt **SQLite-backed durable queue** in core service with worker pools and category-specific concurrency controls.

## Policy
- Global default active jobs: 4
- Optional caps per workload type (OCR, ASR, enrichment)
- Retry with bounded backoff and dead-letter state

## Sources
- https://python-rq.org/
- https://docs.celeryq.dev/
- https://dramatiq.io/guide.html
