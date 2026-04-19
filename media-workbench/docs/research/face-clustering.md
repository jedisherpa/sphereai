# Wave 1 Research: Face Clustering (No Identity Recognition)

## Options considered
1. Face detection + embeddings + local clustering for recurring groups
2. Detection-only (no clustering)
3. Any identity matching against known persons (rejected)

## Recommendation
Implement only **detection + same-dataset clustering + manual user labels**.

## Safety boundary
- No identity prediction claims.
- No external identity database matching.
- UI must use neutral terms like `face-cluster-12`.

## Deferred selection
Exact detection/embedding library choice deferred to Wave 2 spike due packaging and performance uncertainty.
