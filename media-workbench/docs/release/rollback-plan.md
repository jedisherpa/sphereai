# Rollback Plan

## Trigger conditions
- Critical data corruption risk.
- Job scheduler unrecoverable state regressions.
- Security/privacy regression in local-only boundary.

## Steps
1. Stop service process.
2. Backup current workspace (`raw/`, `derived/`, `app.db`).
3. Restore previous known-good commit and rerun with same workspace.
4. If schema mismatch is suspected, restore `app.db` from backup.
5. Verify `/health`, `/status`, and basic job flow.
