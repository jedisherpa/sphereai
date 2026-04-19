# Wave 1 Research: Optional LLM Connector Layer

## Requirements
- OpenAI-compatible base URL, model, key, optional headers
- Explicit per-job opt-in
- External-use audit flags and logs
- Strict schema validation for enrichment outputs

## Recommendation
Implement a connector abstraction with a **disabled-by-default** global setting and per-job override.

## UX constraints
- Every externally processed result must display `external_compute_used=true`.
- Local-only mode must hard-disable connector invocations.

## Sources
- https://platform.openai.com/docs/guides/migrate-to-responses
- https://platform.openai.com/docs/assistants/how-it-works
