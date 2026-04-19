# Wave 1 Research: Storage and Indexing

## Options considered
1. SQLite + FTS5
2. DuckDB + FTS extension
3. Embedded search engines (e.g., Meilisearch/Tantivy sidecar)

## Evaluation
- **SQLite + FTS5**: excellent embedded stability, minimal ops burden, strong fit for job/metadata index.
- **DuckDB FTS**: promising analytics path, but FTS extension behavior and update semantics are less straightforward for OLTP-style queue metadata.
- **Sidecar search**: unnecessary complexity for v1.

## Recommendation
Use **SQLite + FTS5** for v1 metadata, queue, labels, and full-text index.

## Sources
- https://www.sqlite.org/fts5.html
- https://duckdb.org/docs/stable/core_extensions/full_text_search
