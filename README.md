# codex-research-bootstrap

An OpenAI Codex CLI bootstrap layer for research workflows: statistics,
population science, public health, quantitative research, manuscript drafting,
and reporting-standards compliance. Distributed clone-and-run: there is no
plugin marketplace step, no separate registry, and no maintainer-side
prerequisite beyond a working Codex CLI install. Every non-trivial deliverable
produced inside a project using this bootstrap passes through an
audit-remediate-loop quality-control pattern with six-branch parallel
specialist auditors and a three-round remediation cap.

## Requirements

Three tiers. The installer detects what is present and reports what is missing.

**Required** — installer refuses to proceed if any of these are absent:

| Tool | Purpose | Source |
|---|---|---|
| `git` | Repository operations, provenance trailers, identity-hygiene gate | system package manager |
| OpenAI Codex CLI | The runtime this bootstrap targets | [developers.openai.com/codex](https://developers.openai.com/codex) |
| Python ≥ 3.10 | Installer, identity-hygiene scanner, hooks | [python.org](https://www.python.org/) |

**Detected-recommended** — installer warns once and prints an install hint;
later phases of work will fail without it:

| Tool | Purpose | Install hint |
|---|---|---|
| `uv` | Python environment management for the bundled MCP servers and skill assets | [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/) |

**Detected-optional** — installer warns only when a relevant skill is first
invoked:

| Tool | Triggered by | Purpose |
|---|---|---|
| `pandoc` | `render-manuscript` skill | Markdown → DOCX conversion for manuscript artifacts |
| `ruff` | `code-reviewer` subagent | Style and idiom audit |
| `nbstripout` | Notebook hygiene hooks | Strips notebook metadata before commit |

## Install

```
git clone <repo-url>
cd codex-research-bootstrap
./install.sh        # macOS / Linux
.\install.ps1       # Windows
```

The installer copies bootstrap files into `$CODEX_HOME` (default `~/.codex/`).
It is idempotent: each file is content-hashed; unchanged files are skipped.
When an installed file differs from the bootstrap source, the existing copy is
moved to `<target>/.bootstrap-backups/<timestamp>/` before the new version is
written. Append `--dry-run` to preview the actions without writing anything.

The installer does **not** touch `~/.codex/AGENTS.md`. Configuring that file
is a separate, opt-in step — see the next section.

[INSTALL.md](INSTALL.md) carries the full procedure: the AI-assisted install
prompt (Codex-CLI-specific, 3-stage install + verify + audit), filesystem
verification snippets, the deployed inventory (skills / agents / hooks /
templates), and bundled MCP-server notes.

## Configuring AGENTS.md

The bootstrap ships a sample user AGENTS.md at
[examples/AGENTS.md](examples/AGENTS.md). To activate it, copy or merge its
contents into your `~/.codex/AGENTS.md`. The sample wraps its bootstrap-managed
content in OMX-style mutation markers:

```
<!-- AUDIT-LOOP:AGENTS:START -->
... bootstrap-managed content ...
<!-- AUDIT-LOOP:AGENTS:END -->
```

Keep these markers intact. Future installer updates refresh only the content
between them; any prose you add above the START marker or below the END marker
is preserved across updates.

## Updating

```
git pull
./install.sh        # or .\install.ps1
```

The installer is idempotent on re-run. Unchanged files are skipped; changed
files trigger a backup-then-replace. The AGENTS.md sample is not auto-applied;
re-run the merge step yourself when the upstream sample changes.

## Repository layout

| Path | Purpose |
|---|---|
| [skills/](skills) | Codex skills (methodology, audit, delivery; populated in Phases B–D) |
| [.codex/agents/](.codex/agents) | TOML subagent definitions (six auditors plus supporting specialists) |
| [hooks/](hooks) | Python lifecycle hooks (SessionStart, Stop, PreToolUse, etc.) |
| [templates/](templates) | Manuscript, ADR, DAG, multiple-testing family, and compliance templates |
| [tools/](tools) | Installer, identity-hygiene scanner, project bootstrap utilities |
| [examples/AGENTS.md](examples/AGENTS.md) | Sample `~/.codex/AGENTS.md` for end users |
| [docs/](docs) | Scope, plan, ADRs, research notes, and audit trails |

## Quality control: audit-remediate-loop

Six-branch parallel specialist auditors run against any non-trivial
deliverable: **reproducibility-verifier** (pinned deps, seeds, dataset
checksums, runnable entrypoint), **code-reviewer** (idiom, style, error
handling, types, docstrings), **quant-auditor** OR **epi-auditor** (mutually
exclusive at the calculations branch by cwd-glob dispatch),
**format-auditor** (magic-number policy, template completeness, citation
consistency), and **literature-check** (citation verification against
primary sources). Three-round remediation cap; structured JSON findings;
diff-based remediation; re-audit on each round. See
[docs/SCOPE.md](docs/SCOPE.md) for the canonical description.

## Reporting standards

The applicable standard is declared at the top of each analysis document and
is enforced by the `format-auditor` and `epi-auditor` subagents:

| Study type | Standard |
|---|---|
| Observational | STROBE |
| Randomized controlled trial | CONSORT |
| Diagnostic accuracy | STARD |
| Prediction model | TRIPOD |
| Systematic review / meta-analysis | PRISMA |

## Contributing

Pre-commit identity-hygiene gate is mandatory:

```
pip install pre-commit
pre-commit install
```

The gate runs `python tools/check_identity.py` against staged files and
blocks any commit that contains forbidden tokens (real names, pseudonyms tied
to a single contributor, personal email addresses, OS usernames, workstation
identifiers). You can also run the scanner manually before committing:

```
python tools/check_identity.py
```

Commit style: [Conventional Commits](https://www.conventionalcommits.org/).
One logical change per commit. License: MIT — see [LICENSE](LICENSE).

## AI-assistance disclosure

Per the [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/),
AI cannot be an author of a deliverable; AI use must be disclosed.
Deliverables produced with AI assistance include an AI-assistance statement
in the README or appendix listing the models used (with version), the role
they played (idea, code, prose, audit), and the path to the reproducibility
log. The bootstrap's `commit-with-provenance` skill threads an
`AI-Assistance` trailer into every commit produced under it.

## References

- [docs/SCOPE.md](docs/SCOPE.md) — mission, audit-remediate-loop,
  de-identification commitment, reporting standards, reproducibility envelope.
- [docs/plan_2026-05-18.md](docs/plan_2026-05-18.md) — six-phase implementation
  plan, validation gates, decision-capture map.
- [docs/decisions/0001-repo-scope-and-naming.md](docs/decisions/0001-repo-scope-and-naming.md) —
  scope, self-containment, and de-identification ADR.
- [docs/research/codex_feature_map_2026-05-18.md](docs/research/codex_feature_map_2026-05-18.md) —
  Codex CLI surface-by-surface map (AGENTS.md walk, skills layout, hooks,
  MCP, subagents).
- [docs/research/survey_codex_cli_bootstrap_repos_2026-05-18.md](docs/research/survey_codex_cli_bootstrap_repos_2026-05-18.md) —
  ecosystem survey and design patterns.
- [docs/research/literature_research_workflow_bootstraps_2026-05-18.md](docs/research/literature_research_workflow_bootstraps_2026-05-18.md) —
  reproducibility and audit-loop literature.
