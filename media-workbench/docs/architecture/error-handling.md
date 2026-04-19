# Error Handling

- Worker errors are captured as `last_error` on job rows.
- Retryable failures transition to `retrying`.
- Non-retryable or max-attempt failures transition to `failed`.
- Derived artifact writes are scoped per asset to avoid cross-asset corruption.
