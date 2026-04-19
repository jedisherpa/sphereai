# ADR-0004: Model Delivery Strategy

## Status
Accepted

## Decision
Use slim app installer + first-run model download manager with optional offline bundle.

## Consequences
- Better installer size.
- Requires resilient download/checksum and cache-repair logic.
