# Wave 3 Risks

- HTTP API currently has no authentication layer (acceptable for local-only loopback, must be hardened later).
- Cancellation is cooperative and not yet preemptive for long-running real model jobs.
- Search currently uses simple LIKE index table, not FTS.
