---
name: validate-data
description: Validate an incoming dataset against schema, distribution, and provenance expectations before any downstream analysis.
---

# Validate Data

## When to invoke
Any time a new CSV/Parquet/HDF/SQL pull enters the project, before it is used in an analysis.

## Checks (run in order; each must pass or surface)

### 1. Provenance
- Source URI, retrieval timestamp, retriever identity (script path + git HEAD).
- License / use restriction captured.
- SHA-256 of raw file logged to `data/_manifest.json`.

### 2. Schema
- Column names, types, nullability vs declared schema (pandera / pydantic).
- Fail on any deviation; do not silently coerce.

### 3. Distribution
- Per-column summary: n, n_missing, dtype, range, top-k cardinality.
- Drift vs prior snapshot if present: PSI or KS per numeric column.
- Flag any column with PSI > 0.25 (Siddiqi 2006) or KS p < 0.01.

### 4. Referential integrity
- PK uniqueness, FK coverage, date ordering (if time-indexed).
- No duplicate (id, timestamp) rows.

### 5. Business rules
- Domain-specific invariants (prices > 0, returns ∈ reasonable range, age < 120, etc.). Keep the invariant list in `data/expectations.yaml`.

## Output
`data/validation_{dataset}_{YYYY-MM-DD}.md` containing:
- Pass/fail per check
- Numerical summaries
- Diffs vs prior snapshot
- Any auto-quarantined rows (with reason)

## Gate
Downstream skills (statistical-analysis, etc.) must not be invoked on a dataset that failed any critical check — raise to the user first.
