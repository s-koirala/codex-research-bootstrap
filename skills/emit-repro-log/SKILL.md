---
name: emit-repro-log
description: Emit a ReproLog JSON record before any artifact write to `artifacts/` or `logs/`. Provides a reproducibility envelope (git HEAD, pip freeze SHA-256, dataset checksums, RNG seed, model hash, runtime stack) for every run. Invoke at the start of any bootstrap, backtest, inference, validation, or delivery operation.
---

# emit-repro-log

## When to invoke

Before any run that writes to `artifacts/` or `logs/`. This includes:

- Any backtest, inference, or validation run.
- Any pre-registration freeze (`pre-register-hypothesis` skill).
- Any analysis output bundled by `deliver-results`.
- Any commit that uses `commit-with-provenance` (which reads the most-recent
  log and emits provenance trailers).

Skip for transient EDA / scratch operations that produce no tracked
artifact.

## Field contract

The record is a JSON object with **13 core fields plus a 4-field `runtime`
sub-object** (added per the 2026-05-18 runtime-stack augmentation). The
canonical schema is at [assets/repro_log_schema.json](assets/repro_log_schema.json);
the emitter is at [assets/emit_repro_log.py](assets/emit_repro_log.py).

### Core 13 fields

| Field | Type | Semantics |
|---|---|---|
| `run_id` | str | ULID (preferred) or uuid4 hex; lexical-sort property convenient but not required |
| `phase` | str | Suggested values: `bootstrap`, `backtest`, `inference`, `validation`, `deliver` — not enum-constrained for forward compatibility |
| `hypothesis_id` | str | HID e.g. `H055`, or `n/a` for non-hypothesis-bound work |
| `timestamp_utc` | str | ISO 8601, microsecond precision |
| `git_head` | str | 40-hex SHA of HEAD; `"unknown"` if outside a git repo |
| `pip_freeze_sha256` | str | **Full 64-hex SHA-256** of `uv pip freeze` (or `pip freeze`) stdout. NOT a truncated cache digest. |
| `pip_freeze_path` | str | Project-relative POSIX path to the captured freeze text (typically `logs/reproducibility/env/<sha>.txt`) |
| `dataset_checksums` | dict<str,str> | Per-file SHA-256 from `data/_manifest.json` (when present) |
| `rng_seed` | int | Explicit seed used; `0` if no sampling |
| `model_hash` | str \| null | Model commit / weight SHA when applicable |
| `config_resolved_sha256` | str \| null | SHA-256 of resolved config snapshot (e.g., frozen `design.md` content) |
| `host` | dict<str,str> | `{os, python, cpu}` — `platform.python_version()` for `python` (version only) |
| `env_id` | str | `file_sha256(uv.lock)` if present; else `"no-uv-lock"` |

### Runtime sub-object (4 fields)

Added 2026-05-18 to capture the OS/interpreter/container stack a record
was emitted under — necessary for true binary reproducibility per Boettiger
(2015), "An introduction to Docker for reproducible research," *ACM SIGOPS
Oper. Syst. Rev.* 49(1):71–79.
[doi:10.1145/2723872.2723882](https://doi.org/10.1145/2723872.2723882). The
core `host` field carries only `python_version()` + `system()`/`release()` +
`machine()`; that is insufficient to reconstruct the execution environment
when the OS distribution, glibc version, or container image changes
underneath. The four new fields close that gap.

| Field | Type | Semantics |
|---|---|---|
| `runtime.python_version` | str | `sys.version` — full version string including build/compiler info |
| `runtime.platform` | str | `platform.platform()` — single-string composite (system + release + version + machine) |
| `runtime.container_digest` | str \| null | Docker/Podman image SHA-256 digest when running inside a container; `null` otherwise or when the digest cannot be read |
| `runtime.os_release` | str | OS-release identifier — Linux `/etc/os-release` `PRETTY_NAME`, Windows `platform.win32_ver()` joined, macOS `platform.mac_ver()` joined |

## Atomic write semantics

Implemented in [assets/emit_repro_log.py](assets/emit_repro_log.py)
`ReproLog.write()`:

```
NamedTemporaryFile(mode='wb', delete=False, dir=path.parent, prefix=f'.{name}.', suffix='.tmp')
  -> write bytes -> flush -> os.fsync(fd) -> close
os.replace(tmp.name, path)   # atomic on POSIX and Windows (MoveFileEx)
```

Constraints:

- Same-volume placement (`dir=path.parent`) — `os.replace` is atomic only
  within a single filesystem.
- Binary mode (`'wb'`) — Windows text-mode CRLF translation would
  invalidate byte-identity SHA-256.
- `delete=False` — Windows cannot reopen a delete-on-close tempfile.
- `os.fsync(tf.fileno())` — flushes the OS write cache to disk; required
  for crash safety.

Crash window: SIGKILL strictly between write and `os.replace` may leave the
tempfile on disk; the target is untouched. This is an accepted limit of
POSIX semantics.

## Project-root discovery

`ProjectPaths.discover()` resolves the project root in this order:

1. `$CODEX_PROJECT_DIR` environment variable, if set (Codex CLI convention).
2. `$CLAUDE_PROJECT_DIR` environment variable, if set (Claude Code
   convention; preserved for cross-tool parity).
3. Ancestor walk from the start directory looking for one of:
   `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements.txt`,
   `Pipfile.lock`, `.git`.
4. Fallback: the current working directory.

## Filename convention

`logs/reproducibility/repro_log_{run_id}.json`. The freeze text is sidecar
at `logs/reproducibility/env/{pip_freeze_sha256}.txt`.

## CLI

```
python skills/emit-repro-log/assets/emit_repro_log.py --selftest
```

Builds a fixture record from the current environment, writes it, reads it
back, and verifies round-trip identity. Exits 0 on success.

## Hand-off

- Consumed by the `commit-with-provenance` skill: reads the most-recent
  log under `logs/reproducibility/` and emits `Repro-Log-Path:` and
  `Repro-Log-SHA256:` commit trailers.
- Hand-off to [audit-remediate-loop](../audit-remediate-loop/SKILL.md) when
  used inside that loop's per-deliverable audit.

## References

- Sandve, Nekrutenko, Taylor, Hovig (2013). "Ten Simple Rules for
  Reproducible Computational Research." *PLOS Comput Biol* 9(10):e1003285.
  [doi:10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).
- Boettiger (2015). "An introduction to Docker for reproducible research."
  *ACM SIGOPS Oper. Syst. Rev.* 49(1):71–79.
  [doi:10.1145/2723872.2723882](https://doi.org/10.1145/2723872.2723882).
  Motivates the `runtime` sub-object.
- Wilkinson et al. (2016). "The FAIR Guiding Principles for scientific data
  management and stewardship." *Sci. Data* 3:160018.
  [doi:10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18).
- Python `os.replace` documentation: atomicity guarantees on POSIX and on
  Windows (MoveFileEx).
- Repository operating instructions:
  [AGENTS.md](../../AGENTS.md) "Reproducibility" section.
