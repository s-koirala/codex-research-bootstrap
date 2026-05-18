---
name: commit-with-provenance
description: Commit staged changes with a Conventional-Commits subject plus provenance trailers (Repro-Log-Path + Repro-Log-SHA256 + AI-Assistance per ICMJE 2026). Recomputes pip freeze inline; never reads a truncated SessionStart cache.
---

# commit-with-provenance

## Usage

```
commit-with-provenance <subject> --role={idea|code|prose|audit|multi} [--scope-strict] [--no-repro <justification>] [--dry-run]
```

## Behavior

Run the wrapper script with the supplied arguments:

```
python tools/commit_with_provenance.py <args>
```

Behavior summary:

1. Reject if no staged changes.
2. Validate the subject matches the Conventional Commits 1.0.0 regex (`feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`).
3. In a publishing cwd (path matches any of the globs `**/manuscript*/**`, `**/publication*/**`, `**/*-paper/**`, or any other glob the project's `AGENTS.md` adds to the publishing-cwd list): require `--role` unless `--no-repro` is set with a justification.
4. Recompute `pip freeze` inline via the project venv (`.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on POSIX). Falls back to `uv pip freeze` if `uv.lock` is present. **Never reads the SessionStart provenance cache** — that cache stores only a 12-hex truncated digest, insufficient for the 64-hex SHA-256 the ReproLog schema requires.
5. Write the freeze text to `logs/reproducibility/env/<sha256>.txt` (project-local).
6. Read `data/_manifest.json` for the `dataset_checksums` map; pass to [emit-repro-log](../emit-repro-log/SKILL.md).
7. Emit a ReproLog at `logs/reproducibility/repro_log_<run_id>.json`.
8. Compose the Conventional Commits subject + trailers:
   - `Repro-Log-Path: <relative path>`
   - `Repro-Log-SHA256: <64-hex of log content>` (content-addressed; tamper-detectable)
   - `AI-Assistance: <model-id> (role=<role>)` per [ICMJE 2026](https://www.icmje.org/recommendations/).
9. `git commit -F <message-file>`.

## Fail-hard conditions

- No staged changes → exit 1.
- Non-Conventional-Commits subject → exit 1.
- No project Python venv detected AND `--no-repro` not set → exit 2; hint to run `bootstrap-project --venv`.
- `--role` missing in a publishing cwd → exit 1.

## Hand-off

- Consumes [emit-repro-log](../emit-repro-log/SKILL.md).
- Consumes `data/_manifest.json` from [tools/build_data_manifest.py](../../tools/build_data_manifest.py).
- Used by every artifact-producing workflow downstream.
