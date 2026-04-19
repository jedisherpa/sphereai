# Settings Guide

Settings are persisted in SQLite `settings` table.

Supported keys:
- `max_concurrency` (int)
- `allow_external_enrichment` (bool)

Update settings:
- POST `/settings` with JSON body.
