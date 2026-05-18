# AGENTS.md — codex-research-bootstrap

Operating instructions for Codex CLI when working **inside this repository**
(i.e., when a contributor is iterating on the bootstrap layer itself). This
file is **not** the sample that ships to end users — that lives at
[examples/AGENTS.md](examples/AGENTS.md) and is intended for a colleague's
own `~/.codex/AGENTS.md`.

## What this repo is

A clone-and-run OpenAI Codex CLI bootstrap layer for research workflows in
statistics, population science, public health, manuscript drafting, and
results compilation. Distribution model: a research colleague clones the
repository and runs the installer; no plugin marketplace, no separate
registry, no maintainer-side prerequisite beyond Codex CLI itself. The
repository is self-contained — the audit-remediate-loop skill, the six
specialist auditor subagents, every referenced methodology skill, and every
template ship inside this tree rather than in a personal `~/.codex/` setup.

The canonical scope statement and quality-control commitment live in
[docs/SCOPE.md](docs/SCOPE.md). The repo-scope and self-containment decision
is recorded in
[docs/decisions/0001-repo-scope-and-naming.md](docs/decisions/0001-repo-scope-and-naming.md).
The six-phase implementation plan is in
[docs/plan_2026-05-18.md](docs/plan_2026-05-18.md).

## Operating posture

**Dependency posture.** `tools/install.py` and `tools/check_identity.py`
use the Python standard library only, so a fresh clone runs them without a
`pip install` step. Other Python — under `skills/<name>/assets/`,
`hooks/<name>.py`, the rest of `tools/` — may use third-party dependencies,
but each such file documents its own dependency list in a header comment or
sibling `requirements.txt`. When adding new code, prefer stdlib for anything
on the installer or pre-commit path; reserve third-party deps for skill
assets and analysis pipelines.

**Idempotency.** Both `tools/install.py` and `tools/bootstrap_project.py`
are idempotent. A re-run with no changes performs no writes. When a
destination file differs from the bootstrap source, the existing copy is
moved to `<target>/.bootstrap-backups/<timestamp>/` before the new version
is written; the script never silently overwrites user content.

**Atomic writes.** Every write to a file under `$CODEX_HOME` or
`<project>/.codex/` uses the temp-file-then-rename idiom: write the new
content to a sibling temp file, fsync, then rename onto the destination
path. The canonical pattern is in `tools/install.py` and is reused by
`skills/emit-repro-log/assets/emit_repro_log.py`. When authoring new write
paths, follow the same pattern.

## De-identification commitment

Absolute. See
[docs/decisions/0001-repo-scope-and-naming.md](docs/decisions/0001-repo-scope-and-naming.md)
for the rationale. Committed files must not contain real names, contributor
pseudonyms tied to a single individual, personal email addresses, OS
usernames or workstation identifiers, or maintainer-specific project tokens.

The pre-commit gate is enforced by `tools/check_identity.py`, which loads
its forbidden-token list from its own source. When working in this repo,
Codex must not paste any literal Windows path containing a username (e.g.,
the contributor's `C:\Users\<name>\` prefix), any contributor pseudonym,
any personal-email-TLD address, or any maintainer-specific project token
into a committed file. If a contributor's working tree path appears in a
draft file, normalize it to a placeholder before staging.

When adding new content that references file paths, prefer repo-relative
paths (`tools/install.py`) or `$CODEX_HOME`-relative paths
(`$CODEX_HOME/skills/<name>/`) over absolute paths.

## Audit-remediate-loop

Every non-trivial deliverable in this repository (>20 lines of new code or
prose, or any new statistical method) passes through the audit-remediate-loop.
The skill lives at `skills/audit-remediate-loop/SKILL.md`; the operating
pattern is described in [docs/SCOPE.md](docs/SCOPE.md) and is summarized
here.

Six specialist auditor subagents run in parallel against the deliverable:

- **reproducibility-verifier** — pinned dependencies, seeds, dataset
  checksums, runnable entrypoint, ReproLog envelope.
- **code-reviewer** — idiom, style, design patterns, error handling, type
  hints, docstring completeness.
- **quant-auditor** — statistical method fidelity, numerical correctness,
  time-series integrity for quant cwds.
- **epi-auditor** — DAG declaration, back-door adjustment-set selection,
  E-value sensitivity, reporting-standard coverage for epi cwds.
- **format-auditor** — magic-number policy, template-substitution
  completeness, citation-format consistency, docstring style.
- **literature-check** — citation verification against primary sources.

The quant-auditor and epi-auditor are mutually exclusive at the calculations
branch: which one engages is determined by cwd-glob dispatch. A deliverable
in a quant cwd is audited by quant-auditor; one in an epi cwd is audited by
epi-auditor. The other four branches always run.

Three-round remediation cap. Multi-agent self-consistency gains taper at
moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751));
three rounds is an operational choice balancing coverage against cost.
Structured JSON findings; diff-based remediation; re-audit on each round.

## Stop-event audit-trail aggregation

Codex CLI has no `SessionEnd` event. The `Stop` event fires once per turn,
not once per session, so a naive port of a session-end audit-trail hook
either emits the trail every turn (wasteful) or never (broken). The
bootstrap's resolution:

- Every `Stop` hook appends a per-turn JSON record to
  `logs/turn_<session_id>_<n>_<ts_us>.json` (see
  `hooks/stop_audit_aggregator.py` for the filename scheme).
- The next `SessionStart` aggregates closed-session turn files into
  `docs/audits/session_trail_<date>_<session_id>.md` and removes the
  per-turn files for the now-closed session. The aggregation half lives in
  `hooks/session_start_provenance.py`.

The Stop-side hook is wired in `.codex/hooks.json` on the `Stop` event; the
SessionStart-side aggregator runs in the same `SessionStart` hook that
emits provenance. The closed-session detection logic treats any
`session_id` other than the new session's `session_id` as closed, so a
restart of Codex flushes the prior session's turn files on its first
turn.

## ReproLog

Every bootstrap, backtest, or inference run emits a JSON ReproLog record to
`logs/reprolog/<run-id>.json`. The record contains:

- `git_head` — the repository HEAD SHA.
- `pip_freeze_sha256` — SHA-256 of the active environment's `pip freeze`
  output.
- `dataset_checksums` — map of dataset paths to their SHA-256 digests.
- `rng_seed` — the seed used for any randomness in the run.
- `model_commit_hash` — the commit hash of any model artifact consumed.

Plus four runtime-stack fields:

- `runtime.python_version` — `sys.version_info` as a string.
- `runtime.platform` — `platform.platform()` output.
- `runtime.container_digest` — container image digest if running in a
  container, else null.
- `runtime.os_release` — contents of `/etc/os-release` on Linux, the
  Windows release tuple on Windows, the macOS version on Darwin.

The schema lives at `skills/emit-repro-log/assets/repro_log_schema.json`.
Writes are atomic via temp-file-then-rename.

## Methodology mandates (inlined rules)

These rules apply when a deliverable is being authored or audited inside a
project whose cwd matches one of the patterns below. The rules are duplicated
here so Codex working inside the bootstrap repository can self-audit any
example artifact or fixture without consulting external files.

### Quant cwds

Glob match: `**/*backtest*/`, `**/*factor*/`, `**/*signal*/`, `**/*strategy*/`.

- **No look-ahead.** Every feature must be computable at time t using only
  data available at time t. Train/val/test splits are time-ordered and
  disjoint; walk-forward cross-validation, never k-fold.
- **Returns.** State log vs. arithmetic and the compounding convention at
  the top of the analysis.
- **Prices.** Adjust for corporate actions before any return calculation.
- **Standard errors.** Newey-West (HAC) with data-dependent bandwidth
  ([Newey & West 1994, DOI 10.2307/2297912](https://doi.org/10.2307/2297912))
  or Andrews parametric plug-in
  ([Andrews 1991, DOI 10.2307/2938229](https://doi.org/10.2307/2938229)).
- **Sharpe confidence intervals.** Single-strategy CI via
  [Opdyke 2007 DOI 10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084)
  or [Lo 2002 DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453).
  Pairwise strategy comparison via studentized time-series bootstrap
  ([Ledoit & Wolf 2008 DOI 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002)).
- **Multiple testing across strategies.** White's reality check
  ([White 2000 DOI 10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152))
  or Hansen's SPA
  ([Hansen 2005 DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063)).
- **Reporting requirements.** Every backtest document lists: universe,
  rebalance frequency, transaction-cost model, survivorship-bias treatment,
  data vendor + snapshot date. Plus performance metrics: Sharpe, Sortino,
  max drawdown, turnover, capacity estimate.
- **Published research.** Any factor, signal, or rule must have a citation
  or a derivation. No unattributed folklore factors.

### Epi cwds

Glob match: `**/epidemiolog*/`, `**/clinical*/`, `**/cohort*/`,
`**/case-control*/`, `**/RCT*/`, `**/diagnostic*/`.

- **Reporting standards.** Declared at the top of the analysis document:
  STROBE (observational), CONSORT (randomized controlled trial), STARD
  (diagnostic accuracy), TRIPOD (prediction model), PRISMA (systematic
  review / meta-analysis).
- **DAG declared before adjustment-set selection.** Use dagitty or plain
  text. The adjustment set is chosen via the back-door criterion (Pearl),
  not a kitchen-sink regression.
- **Sensitivity to unmeasured confounding.** Report the E-value
  ([VanderWeele & Ding 2017, Ann Intern Med 167:268, DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607))
  for each primary causal estimate.
- **Missingness.** Declare the MCAR / MAR / MNAR assumption with evidence.
  Primary analysis: multiple imputation with m ≥ percentage of incomplete
  cases ([White, Royston, Wood 2011, Stat Med 30:377, DOI 10.1002/sim.4067](https://doi.org/10.1002/sim.4067))
  unless MCAR is supported. Complete-case analysis as sensitivity only.
- **PHI handling.** Protected health information must not leave the
  project's data directory. IRB and dataset-use-agreement constraints are
  documented at the project root.

### Publishing mandates

When working on manuscript artifacts (drafts, figures, supplementary
materials, submission packages):

- Every deliverable includes an AI-assistance statement in the README or
  manuscript appendix listing the models used (with version), the role
  they played (idea, code, prose, audit), and the path to the
  reproducibility log.
- Follow the [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/).
  AI cannot be an author. AI assistance must be disclosed.

## Codex CLI conventions used

**AGENTS.md walk.** This file is the top-level prose Codex reads when
operating in this repository. Codex walks from the git root to the current
working directory and concatenates each `AGENTS.md` it encounters, with
closer-to-cwd files appearing later in the combined prompt so they override
earlier guidance. The current repository ships only this top-level
`AGENTS.md`; per-subdirectory `AGENTS.md` files may be added in later phases
(for example, when scaffolded projects under `tests/fixtures/` need
domain-specific guidance).

**32 KiB cap.** Codex applies a `project_doc_max_bytes` cap (default 32 KiB)
across the concatenated AGENTS.md chain. This file targets 12-15 KiB to
leave headroom for per-subdirectory additions deeper in the tree.

**Skills.** Each skill lives at `skills/<name>/SKILL.md` with YAML
frontmatter (`name`, `description`) and optional siblings `scripts/`,
`references/`, `assets/`. Progressive disclosure: Codex sees only `name`
and `description` until the skill is selected; the body loads then;
`scripts/` and `references/` load only when the body invokes them. Keep
`description` exhaustive about firing conditions.

**Subagents.** Each subagent is a TOML file at
`.codex/agents/<name>.toml` with required keys `name`, `description`,
`developer_instructions`. Optional: `model`, `model_reasoning_effort`,
`sandbox_mode`, `mcp_servers`, `skills.config`. All six auditors are
`sandbox_mode = "read-only"`; only remediator steps use
`workspace-write`.

**Hooks.** Event wiring lives in
[.codex/hooks.json](.codex/hooks.json); scripts live under `hooks/<name>.py`.
Events used by this bootstrap: `SessionStart`, `PreToolUse`, `PostToolUse`,
`Stop`. There is no `SessionEnd`; the `Stop`-aggregation pattern above
substitutes. `PermissionRequest` and `UserPromptSubmit` are available
Codex events but are not currently wired by the bootstrap.

**MCP servers.** Declared in [.codex/config.toml](.codex/config.toml) as
`[mcp_servers.<name>]` tables. Two ship by default — `arxiv` (literature
retrieval for `literature-check`) and `crossref` (DOI metadata for
`cite-add`). Both use the `uv tool run` invocation pattern so a fresh
clone resolves the server packages on first use rather than at install
time.

**Permissions.** Bash allow / deny / ask lists live in the
`[permissions]` table of [.codex/config.toml](.codex/config.toml).
Consumers may extend (never weaken) the deny list per-project.

## References

- [docs/SCOPE.md](docs/SCOPE.md) — mission, audit-remediate-loop,
  de-identification, reporting standards, reproducibility envelope.
- [docs/plan_2026-05-18.md](docs/plan_2026-05-18.md) — six-phase
  implementation plan, validation gates, decision-capture map.
- [docs/decisions/0001-repo-scope-and-naming.md](docs/decisions/0001-repo-scope-and-naming.md) —
  repo-scope, self-containment, and de-identification ADR.
- [docs/research/codex_feature_map_2026-05-18.md](docs/research/codex_feature_map_2026-05-18.md) —
  Codex CLI surface-by-surface map and porting notes.
