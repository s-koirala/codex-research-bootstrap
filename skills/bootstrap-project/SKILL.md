---
name: bootstrap-project
description: Scaffold a new project directory with the research-project canonical layout (directory tree + manifest + git init; templated AGENTS.md / README.md / etc.). Use whenever starting a new research project.
---

# bootstrap-project

## Usage

```
bootstrap-project <name> --kind={quant|epi|publishing|generic} [--path=<parent>] [--python-version=X.Y] [--venv] [--user-email=<your-email@your-domain>] [--dry-run] [--rollback-on-fail]
```

## Behavior

Run the bootstrap script with the supplied arguments:

```
python tools/bootstrap_project.py <args>
```

The script renders the directory tree, writes `manifest.json`, and renders ~10 top-level files from templates: `AGENTS.md`, `README.md`, `CHANGELOG.md`, `LICENSE`, `pyproject.toml`, `.gitignore`, `.gitattributes`, `.pre-commit-config.yaml`, `CITATION.cff`, plus kind-specific files (`hypothesis_backlog.md` for quant; `docs/protocol/protocol_v0.md` for epi; `manuscript/manuscript.md` + `docs/ai_assistance_statement.md` for publishing).

### Layout

- Creates `<path>/<name>/` with the base subdir tree plus kind-conditional extras (e.g. `research/01_hypothesis_register/` for quant, `docs/protocol/` for epi, `manuscript/` for publishing). Both `runs/` AND `artifacts/runs/` are emitted (project convention emits both as siblings).
- Writes `manifest.json` at project root: `bootstrap_script_version`, `bootstrap_script_git_head`, `kind`, `rules_file`, `python_version`, `venv_created`, `timestamp_utc`, `subdirs`, `subdir_listing_sha256`, `files: {}`.
- Resolves `python_version` from the bootstrap repo's `pyproject.toml::[project].requires-python` (overridable via `--python-version`).
- If `--venv`: runs `uv venv` in the project root.
- Calls `git init -b main` and an initial Conventional Commits `chore: bootstrap` commit.

### Idempotency

- Re-running on an existing project root with matching `kind` + matching `bootstrap_script_git_head` + matching `subdir_listing_sha256` exits `in-sync` with no writes.
- If the bootstrap-repo HEAD has drifted since last bootstrap (template source changed), exits non-zero with a `--migrate` hint. `--migrate` is reserved for a follow-up phase.
- If subdirs are missing, recreates them and updates the manifest.

### Identity hygiene

- For `--kind=publishing`, pass `--user-email <your-email@your-domain>`. The script writes it to the new repo's local git config; it does NOT modify global git config.
- Per the identity-hygiene reminder in [AGENTS.md](../../AGENTS.md), never auto-set a real-name email anywhere. The flag's value is whatever pseudonymous or project-bound address the user wishes to attach to commits in the new project.

### Rollback

With `--rollback-on-fail`, if any exception fires AFTER `mkdir` but BEFORE successful completion, the script `shutil.rmtree`s the newly-created project directory. It only operates on a directory created in the current invocation; never deletes a pre-existing tree.

## Reproducibility

- The bootstrap manifest records the bootstrap-repo HEAD at bootstrap time, so any future audit can reproduce the layout by checking out that SHA and re-running.
- Every templated file additionally has its rendered SHA-256 recorded under `manifest.files`.

## Hand-off

- After bootstrap, the user can invoke the [adr-new](../adr-new/SKILL.md) skill to seed `docs/decisions/ADR-0001.md`.
- For `--kind=quant`: use the [hypothesis-new](../hypothesis-new/SKILL.md) skill to populate `hypothesis_backlog.md`.
- All subsequent commits in the bootstrapped project should use the [commit-with-provenance](../commit-with-provenance/SKILL.md) skill.
