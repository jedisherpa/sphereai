# ADR-0002: Durable Queue State Machine

## Status
Accepted

## Decision
Adopt explicit job states (`pending`, `running`, `completed`, `failed`, `canceled`, `retrying`) with bounded retries and per-job logs.

## Consequences
- Better crash recovery and user-visible failure management.
- Slightly more schema and orchestration complexity.
