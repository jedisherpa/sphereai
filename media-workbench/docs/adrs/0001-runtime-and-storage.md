# ADR-0001: Runtime and Storage Baseline

## Status
Accepted

## Decision
Use local backend + SQLite index + filesystem-first artifact storage.

## Consequences
- Simple install story and offline-capable core.
- Requires robust migration strategy as schema evolves.
