---
name: preregister
description: Freeze the design.md for a hypothesis ID. Renders the 11-section template, computes its SHA-256, emits a ReproLog with config_resolved_sha256 = design.md SHA, and commits via commit-with-provenance. Use after hypothesis-new and before power-analysis.
---

# preregister

## Usage

```
preregister <HID> [--force] [--external=osf]
```

## Behavior

Invoke the [pre-register-hypothesis](../pre-register-hypothesis/SKILL.md) skill on the specified hypothesis ID. The model executes these steps by reading that SKILL.md:

1. Locate the project (walk up from cwd for `.git` / `pyproject.toml` / `uv.lock`).
2. Read `hypothesis_backlog.md`; verify the H<NNN> row exists with status `designed`.
3. Render `skills/pre-register-hypothesis/assets/hypothesis_design_TEMPLATE.md` with `{HID}` / `{TITLE}` / `{TIER}` / `{DATE}` / `{CITATIONS}` substitutions.
4. Prompt the user for the 11-section content (or accept it from supplied context).
5. Write to `research/01_hypothesis_register/<HID>/design.md`. Refuse overwrite without `--force`.
6. Compute `design.md` SHA-256.
7. Invoke [emit-repro-log](../emit-repro-log/SKILL.md) with `phase=validation`, `hypothesis_id=<HID>`, `config_resolved_sha256=<sha>`.
8. Update the backlog row: append `frozen_sha256=<sha[:12]>` to the row's `Notes` cell.
9. Stage `research/01_hypothesis_register/<HID>/design.md` + `hypothesis_backlog.md`.
10. Run `commit-with-provenance "feat(pre-reg): freeze <HID> design.md" --role=prose`.
11. If `--external=osf` is passed AND OSF MCP is wired in: upload to OSF as a private project, capture the DOI, and add to `design.md` frontmatter `external_doi:`. Default: internal-only (no external posting); the design.md SHA in the ReproLog is the tamper-evident freeze record.

## Fail-hard conditions

- HID not in backlog → exit 1 with hint to run the `hypothesis-new` skill first.
- Status not `designed` (e.g. already `running` or `archived`) → exit 1, advise creating a new HID.
- `design.md` already exists and `--force` not set → exit 1.

## Reproducibility

The freeze ReproLog is the tamper-evident anchor. To later verify that a design was not modified after freeze, recompute the `design.md` SHA-256 and compare to the ReproLog's `config_resolved_sha256`.

External pre-registration: OSF is the default if a token is available; arXiv requires endorsement and is deferred. Internal-only fallback (no external posting) is fully reproducible from the ReproLog alone.
