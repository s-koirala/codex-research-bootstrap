# Inventory of the Claude Code customization layer for Codex CLI porting (2026-05-18)

## Provenance

The source customization root is the maintainer's per-user Claude Code
configuration directory (referred to throughout this document as
`~/.claude/`, the POSIX-style abstraction). Enumeration was performed by
listing files via Glob, reading file content via Read, and grepping
content via Grep. File sizes and last-modified dates were captured via
PowerShell `Get-ChildItem`.

This document is the resolution of the "open question" in
[codex_feature_map_2026-05-18.md](codex_feature_map_2026-05-18.md):
whether a single SKILL.md tree can be deployed to both Claude Code and
Codex CLI. It also classifies every customization component into one of
PORT / LOCAL-ONLY / PARTIAL and identifies blockers to address before
implementation.

## Method

1. Enumerated each customization surface (skills, agents, hooks,
   commands, rules, scripts, templates, settings, MCP) with size and
   date metadata.
2. Read each source file once. For skills, the 14 SKILL.md files
   (entire skill catalog — no sampling required given small N) were
   scanned line by line for tool references and identity-bound strings.
3. Classified each artifact by porting disposition:
   - **PORT** — research- or QC-oriented, identity-neutral.
   - **PARTIAL** — substantively useful but contains identity or
     surface-system-specific content requiring de-identification or
     schema conversion.
   - **LOCAL-ONLY** — identity-bound, user-specific, or out of scope for
     the de-identified Codex CLI bootstrap.
4. Resolved the shared-SKILL.md question by counting Claude-specific
   tool references vs shared / tool-agnostic references and computing
   the rewrite share.
5. Surfaced blockers — hardcoded paths, identity references, embedded
   credentials.

All identifying substrings were removed from this document before
finalization. The verification step grepped the draft for any
pseudonym, OS-username path prefix (Windows or POSIX user-home roots),
or maintainer email; any match would trigger a section rewrite before
commit.

## Inventory

### Skills (`~/.claude/skills/`)

Fourteen skills, each a directory with a `SKILL.md` plus optional
`assets/`. Frontmatter pattern: YAML `name` + `description`.

| Skill | SKILL.md size | Last modified | Assets present | One-line role |
|---|---|---|---|---|
| audit-remediate-loop | 5,151 B | 2026-05-15 | none | 5-branch parallel-auditor QC loop, 3-round cap |
| bayesian-workflow | 11,195 B | 2026-05-15 | none | Gelman 2020 workflow (prior PC, NUTS, R-hat, LOO) |
| deliver-results | 7,219 B | 2026-05-15 | 5 files | Publication figures, workbook, report card, style |
| emit-repro-log | 4,653 B | 2026-05-15 | 3 files | 13-field ReproLog atomic-write emitter |
| mediation-analysis | 8,434 B | 2026-05-15 | none | VanderWeele NDE/NIE counterfactual mediation |
| meta-analysis | 10,771 B | 2026-05-15 | none | Random-effects, HKSJ, forest plot, Egger |
| multiple-imputation | 8,598 B | 2026-05-15 | none | MICE per Rubin's rules; MAR assumption |
| multipletest-gate | 4,809 B | 2026-05-15 | none | Hansen-SPA / White-RC / BH-FDR / Holm gate |
| pit-canary | 6,669 B | 2026-05-15 | none | Point-in-time leakage canaries for backtests |
| power-analysis | 6,720 B | 2026-05-15 | none | Pre-data sample-size; prohibits retro-power |
| pre-register-hypothesis | 5,343 B | 2026-05-15 | 1 file | Freeze the 11-section design.md (quant) |
| statistical-analysis | 4,489 B | 2026-05-15 | none | Assumption check, method select, inference |
| survival-analysis | 7,053 B | 2026-05-15 | none | KM, log-rank, Cox PH, AFT, Schoenfeld |
| validate-data | 1,522 B | 2026-04-15 | none | Schema + distribution + provenance gate |

Assets total an additional ~80 KB across the `deliver-results`,
`emit-repro-log`, and `pre-register-hypothesis` skill directories.

### Subagents (`~/.claude/agents/`)

Seven markdown files. Frontmatter pattern: `name`, `description`, `tools`
(comma-separated), `model: inherit`. Body is the system prompt.

| Subagent | Size | Last modified | Tools declared | Role |
|---|---|---|---|---|
| code-reviewer | 4,600 B | 2026-05-15 | Read, Grep, Glob | Idiom/types/error-handling code review |
| dag-drafter | 3,951 B | 2026-05-15 | Read, Grep, Glob, Write, WebFetch | dagitty DAG + back-door adjustment set |
| epi-auditor | 6,099 B | 2026-05-15 | Read, Grep, Glob, WebFetch | DAG + E-value + STROBE/CONSORT/STARD/TRIPOD coverage |
| format-auditor | 5,446 B | 2026-05-15 | Read, Grep, Glob | Magic-numbers + identity hygiene + template-substitution |
| literature-check | 1,913 B | 2026-04-15 | Read, Grep, Glob, WebFetch, WebSearch | Citation verification against primary sources |
| quant-auditor | 2,735 B | 2026-04-15 | Read, Grep, Glob, Bash | Method fidelity + leakage + numerical correctness |
| reproducibility-verifier | 2,118 B | 2026-04-15 | Read, Grep, Glob, Bash | Deps pinning + seeds + checksums + entrypoint |

Each agent declares structured JSON output schema; severities use the
critical / major / minor rubric uniformly.

### Hooks (`~/.claude/hooks/`)

Eight Python files (one is a compiled `.pyc` cache, excluded). All
invoked from `settings.json` `hooks` block.

| Hook | Size | Last modified | Event | Identity / system coupling |
|---|---|---|---|---|
| session_start_provenance.py | 4,500 B | 2026-04-15 | SessionStart | Uses `CLAUDE_PROJECT_DIR` env; caches under `~/.claude/cache/` |
| session_end_audit_log.py | 2,152 B | 2026-04-15 | SessionEnd | Uses `CLAUDE_PROJECT_DIR`; writes `docs/audits/session_trail_{date}.md` |
| pre_bash_safety.py | 2,151 B | 2026-04-15 | PreToolUse(Bash) | None (env-only via `CLAUDE_PROJECT_DIR`) |
| pre_write_seed_guard.py | 15,836 B | 2026-04-15 | PreToolUse(Write/Edit/MultiEdit/NotebookEdit) | None |
| pre_write_phi_guard.py | 8,397 B | 2026-05-15 | PreToolUse(Write/Edit/MultiEdit/NotebookEdit) | Cwd-globbed; matches population-health project paths |
| post_write_notebook_clean.py | 986 B | 2026-04-15 | PostToolUse(Write/Edit/NotebookEdit) | None |
| precommit_seed_guard.py | 10,308 B | 2026-04-15 | (external) pre-commit hook | None |
| precommit_citation_cff.py | 4,554 B | 2026-05-15 | (external) pre-commit hook | None |

`settings.json::hooks` block wires the in-session hooks; the two
`precommit_*.py` hooks are invoked from a project-level
`.pre-commit-config.yaml` rather than from Claude Code itself. The Codex
CLI feature map confirms that Codex has no `SessionEnd` equivalent — the
closest is the per-turn `Stop` event, which fires on every turn.

### Slash commands (`~/.claude/commands/`)

Ten markdown files, each with YAML frontmatter (`description`,
`argument-hint`) plus a body describing the command's behavior.

| Command | Size | Last modified | Role |
|---|---|---|---|
| adr-new.md | 2,640 B | 2026-05-15 | Auto-numbered ADR creation from template |
| audit-loop.md | 647 B | 2026-04-15 | Invoke the audit-remediate-loop skill |
| bootstrap-project.md | 3,351 B | 2026-05-15 | Scaffold a new research project (kind=quant/epi/publishing/generic) |
| cite-add.md | 2,667 B | 2026-05-15 | Resolve DOI via CrossRef MCP and append to CITATION.cff |
| commit-with-provenance.md | 2,544 B | 2026-05-15 | Conventional Commits + Repro-Log + AI-Assistance trailers |
| hypothesis-new.md | 3,504 B | 2026-05-15 | Append HID to hypothesis_backlog.md (quant workflow) |
| lit-check.md | 364 B | 2026-04-15 | Spawn the literature-check agent |
| preregister.md | 2,403 B | 2026-05-15 | Freeze design.md via pre-register-hypothesis skill |
| render-manuscript.md | 3,307 B | 2026-05-15 | Pandoc render md → docx via reference.docx |
| reproduce.md | 514 B | 2026-04-15 | Spawn the reproducibility-verifier agent |

The Codex CLI feature map flagged custom prompts as deprecated; commands
must port to skill files, not Codex's `prompts/` directory. Several
commands invoke Python scripts and templates under `~/.claude/scripts/`
and `~/.claude/templates/` (enumerated below); per the ADR's
self-containment principle, these must be ported into the bootstrap repo
rather than referenced from the source customization root.

### Rules (`~/.claude/rules/`)

Three cwd-scoped rule files, imported into the top-level instruction
file via `@`-style directives in the source system.

| Rule | Size | Last modified | Cwd-glob scope |
|---|---|---|---|
| population-health.md | 1,161 B | 2026-04-15 | Epidemiology project paths |
| publishing.md | 1,089 B | 2026-04-15 | Manuscript / publication project paths |
| quant-project.md | 1,704 B | 2026-04-20 | Quant / factor / backtest project paths |

These contain reporting-standard mandates (STROBE / CONSORT / STARD /
TRIPOD / PRISMA), HAC standard-error policy, Sharpe-CI methodology, and
identity-hygiene policy for the publishing rule. The
[ADR](../decisions/0001-repo-scope-and-naming.md) requires the Codex
port to inline equivalent rules into AGENTS.md per-subdirectory rather
than rely on `@import`.

### Scripts (`~/.claude/scripts/`)

Five Python scripts plus a `bootstrap_templates/` subdirectory of 12
`*.tmpl` files (17 files total). Consumed by slash commands and by the
pre-commit hook chain.

| File | Role |
|---|---|
| bootstrap_project.py | Scaffold a new project working directory (consumed by `/bootstrap-project`); writes `manifest.json`, optionally renders bootstrap_templates/. |
| commit_with_provenance.py | Conventional Commits + ReproLog trailers (consumed by `/commit-with-provenance`). Recomputes pip freeze inline. |
| render_manuscript.py | Pandoc md → docx via `templates/manuscript/reference.docx` (consumed by `/render-manuscript`); emits sidecar render log. |
| build_manuscript_reference.py | Generates the pandoc reference.docx (minimalist B&W; major-journal compatible). |
| build_data_manifest.py | Walks `data/{raw,interim,processed,external}/`, writes/checks `data/_manifest.json` per `templates/data_manifest_schema.json`. |
| bootstrap_templates/CLAUDE.md.tmpl | Project-local CLAUDE.md template referencing the cwd-scoped rules file. |
| bootstrap_templates/README.md.tmpl | Project README skeleton with status table and layout placeholder. |
| bootstrap_templates/pyproject.toml.tmpl | uv-managed Python project skeleton; `<<AUTHOR>>` placeholder. |
| bootstrap_templates/.gitignore.tmpl | Standard secrets + Python + notebook ignore patterns. |
| bootstrap_templates/.pre-commit-config.yaml.tmpl | Pinned pre-commit hooks: ruff / nbstripout / nbqa / seed-guard / citation-cff / data-manifest-check. |
| bootstrap_templates/CHANGELOG.md.tmpl | Keep-a-Changelog 1.1.0 + SemVer 2.0.0 skeleton. |
| bootstrap_templates/LICENSE.tmpl | MIT license skeleton with `<<AUTHOR>>` / `<<YEAR>>` placeholders. |
| bootstrap_templates/.gitattributes.tmpl | Text/binary classification + nbstripout notebook filter. |
| bootstrap_templates/hypothesis_backlog.md.tmpl | Append-only hypothesis register (quant workflow). |
| bootstrap_templates/protocol_v0.md.tmpl | Study-protocol skeleton with `reporting_standard:` field. |
| bootstrap_templates/manuscript.md.tmpl | Manuscript skeleton with abstract / introduction sections. |
| bootstrap_templates/ai_assistance_statement.md.tmpl | ICMJE 2026 AI-assistance disclosure skeleton. |

### Templates (`~/.claude/templates/`)

Twelve template files (top-level + `compliance/` + `manuscript/`
subdirectories), consumed by slash commands and skills.

| File | Role |
|---|---|
| CITATION.cff.tmpl | Citation File Format 1.2.0 skeleton with `<<KEY>>` placeholders; consumed by `/cite-add` and the citation-cff pre-commit hook. |
| adr_TEMPLATE.md | ADR skeleton (Context / Decision / Consequences / Alternatives / References); consumed by `/adr-new`. |
| data_manifest_schema.json | JSON Schema 2020-12 spec for `data/_manifest.json`; consumed by validate-data + emit-repro-log. |
| dag_TEMPLATE.dag | dagitty-syntax causal DAG skeleton; consumed by dag-drafter agent. |
| multipletest_family_TEMPLATE.yaml | Multiple-testing family register (append-only); consumed by multipletest-gate skill. |
| compliance/dua_TEMPLATE.md | Data-Use-Agreement skeleton (provider / recipient / dataset description / scope / sanctions). |
| manuscript/reference.docx | Binary pandoc reference document (12pt Times New Roman, double-spaced, 1" margins); consumed by render-manuscript.py. |
| manuscript/manuscript_strobe_TEMPLATE.md | STROBE 2007 observational-study manuscript skeleton. |
| manuscript/manuscript_consort_TEMPLATE.md | CONSORT 2010 RCT manuscript skeleton. |
| manuscript/manuscript_stard_TEMPLATE.md | STARD diagnostic-accuracy manuscript skeleton. |
| manuscript/manuscript_tripod_TEMPLATE.md | TRIPOD prediction-model manuscript skeleton. |
| manuscript/manuscript_prisma_TEMPLATE.md | PRISMA 2020 systematic-review manuscript skeleton. |

### Settings (`~/.claude/settings.json`)

2,006 B, last modified 2026-05-16. JSON schema with these top-level
keys: `cleanupPeriodDays`, `includeCoAuthoredBy`, `permissions`
(allow / deny / ask Bash patterns), `hooks` (Event → matcher → command
mapping for all six in-session hooks above), `effortLevel`. The
`hooks.*.command` values hardcode the maintainer's `C:/Users/<username>/`
Windows path — these are blockers for port.

A second file `settings.local.json` (99 B, 2025-11-27) contains a
single `Bash(cat:*)` allow rule and is gitignored per source-system
convention.

### MCP (`~/.claude/mcp.json`)

2,319 B, last modified 2026-05-15. Registers two MCP servers:

| Server | Command | Tools |
|---|---|---|
| `arxiv` | `uv tool run arxiv-mcp-server` | search_papers, download_paper, list_papers, read_paper, citation_graph |
| `crossref` | `uv tool run crossref-cite-mcp` | DOI → CSL-JSON / BibTeX / RIS resolution |

Tokens are file-referenced via environment variables (`CROSSREF_MAILTO`,
`ARXIV_STORAGE_PATH`), never inlined. The file also lists two
intentionally disabled servers (`zenodo`, `zotero`) with documented
rationale.

The instruction-document analog (referred to here as `~/.claude/CLAUDE.md`)
contains identity-bound prose (a pseudonym, role, professional background,
publication venue list). It is summarized for context here but is
identity-bound and falls in the LOCAL-ONLY bucket.

## Dependency map

Port order matters because most skills cite agents and other skills.
Arrows: `A → B` means "A invokes / depends on B".

```
audit-remediate-loop  → {quant-auditor, epi-auditor, literature-check,
                         reproducibility-verifier, code-reviewer,
                         format-auditor}

Quant chain:
  /hypothesis-new       → /commit-with-provenance
  /preregister          → pre-register-hypothesis → emit-repro-log
                        → /commit-with-provenance
  power-analysis        → emit-repro-log → /commit-with-provenance
                        → quant-auditor
  pit-canary            → quant-auditor (invoker) + emit-repro-log
                        + audit-remediate-loop (failure escalation)
  multipletest-gate     → emit-repro-log + /commit-with-provenance
                        + quant-auditor

Epi chain:
  dag-drafter           → emit-repro-log
  mediation-analysis    → dag-drafter + statistical-analysis
                        + epi-auditor + deliver-results
  multiple-imputation   → statistical-analysis + epi-auditor
  survival-analysis     → power-analysis + multipletest-gate
                        + deliver-results + dag-drafter (epi cwd)
  meta-analysis         → validate-data + deliver-results
                        + bayesian-workflow (random-effects Bayesian)

Cross-cutting:
  statistical-analysis  → audit-remediate-loop (hand-off)
  validate-data         → gate; blocks downstream on failure
  emit-repro-log        → consumed by /commit-with-provenance,
                          deliver-results
  deliver-results       → emit-repro-log + validate-data
                        + audit-remediate-loop

Commands → skills/agents:
  /audit-loop           → audit-remediate-loop
  /lit-check            → literature-check (agent direct)
  /reproduce            → reproducibility-verifier (agent direct)
  /preregister          → pre-register-hypothesis
  /cite-add             → crossref MCP server
  /hypothesis-new       → crossref MCP server + /commit-with-provenance
  /commit-with-provenance, /bootstrap-project, /render-manuscript,
    /adr-new            → external scripts/templates (under
                          ~/.claude/scripts/ and ~/.claude/templates/;
                          see new sections below)
```

**Cross-tree dependencies (port required).** The five Python scripts
and twelve `bootstrap_templates/*.tmpl` files under `~/.claude/scripts/`,
plus the twelve files under `~/.claude/templates/` (including
`adr_TEMPLATE.md`, `CITATION.cff.tmpl`,
`multipletest_family_TEMPLATE.yaml`, the five
`manuscript_*_TEMPLATE.md` files, and the binary `reference.docx`),
exist under the source customization root rather than under the skill,
agent, or hook trees. Per the ADR's self-containment principle, the
bootstrap repo must port them — not reference them — so that a colleague
clone receives a functioning setup without an external `~/.claude/`
dependency.

**Critical port-order implications:** agents port before skills that
invoke them (audit-remediate-loop needs all six auditors available as
Codex subagents per TOML schema); `emit-repro-log` is on the critical
path for downstream skills and commands; `commit-with-provenance` is on
the dependency frontier for every artifact-producing workflow; the
script and template dependencies referenced from slash commands live
under the source customization root and must be ported into the
bootstrap repo per the ADR's self-containment principle.

## Port / local / partial classification

### Skills

| Skill | Disposition | Rationale |
|---|---|---|
| audit-remediate-loop | PARTIAL | One Claude-specific `Agent` tool literal (line 32), one "Claude-3.5-Sonnet" model-name citation in the SciCode benchmark reference (line 69), and `~/.claude/` path references in cross-references — neutralize all three. |
| bayesian-workflow | PORT | Pure methodology. |
| deliver-results | PARTIAL | Assets contain a pseudonym-named style file and identity-bound notes in `report_card_quant.md` — rename + strip. |
| emit-repro-log | PARTIAL | Source code and SKILL.md repeatedly cite the source-system internal library and a GitHub username — strip provenance. |
| mediation-analysis | PORT | Pure methodology. |
| meta-analysis | PORT | Pure methodology. |
| multiple-imputation | PORT | Pure methodology. |
| multipletest-gate | PARTIAL | One absolute `~/.claude/templates/` path reference to `multipletest_family_TEMPLATE.yaml` — the template exists and is PORT-quality, but the path needs to be rewritten to a bootstrap-relative location. |
| pit-canary | PARTIAL | References source-system internal library (`leak_canaries.py`) — strip provenance to generic. |
| power-analysis | PORT | Pure methodology. |
| pre-register-hypothesis | PARTIAL | Frontmatter `owner:` default carries a pseudonym; references a pseudonymized upstream template. |
| statistical-analysis | PORT | Pure methodology. |
| survival-analysis | PORT | Pure methodology. |
| validate-data | PORT | Pure methodology. |

Skills total: **8 PORT, 6 PARTIAL, 0 LOCAL-ONLY** (out of 14).

### Subagents

| Agent | Disposition | Rationale |
|---|---|---|
| code-reviewer | PARTIAL | Universal scope; body references the source-system CLAUDE.md tooling defaults and `memory/` files absent from the bootstrap. |
| dag-drafter | PORT | Pure methodology; references only public primary sources. |
| epi-auditor | PARTIAL | Universal scope; cwd-glob list cites the maintainer's project directory names — generalize. |
| format-auditor | PARTIAL | Universal scope; identity-hygiene policy keyed to a specific dotfiles GitHub username and memory file — generalize. |
| literature-check | PORT | Cwd-agnostic; cites only public evidence-hierarchy guidance. |
| quant-auditor | PORT | Cwd-agnostic. |
| reproducibility-verifier | PORT | Cwd-agnostic; one model-name example to neutralize. |

All 7 agents also need frontmatter conversion from markdown to TOML
per the Codex CLI subagent schema (feature-map item 3) — the
disposition above is content-only; structural conversion is uniform.

Subagents total: **4 PORT, 3 PARTIAL, 0 LOCAL-ONLY** (of 7).

### Hooks

| Hook | Disposition | Rationale |
|---|---|---|
| session_start_provenance.py | PARTIAL | Pure utility; cache path needs generalization to `$CODEX_HOME/cache/`. Re-event for Codex SessionStart. |
| session_end_audit_log.py | PARTIAL | SessionEnd has no Codex equivalent — port to `Stop` with debounce / once-per-turn semantics. |
| pre_bash_safety.py | PORT | Universal Bash safety; no identity. |
| pre_write_seed_guard.py | PORT | AST-driven seed/magic-number guard; no identity. |
| pre_write_phi_guard.py | PARTIAL | Universal pattern; cwd-glob list cites maintainer project names — generalize. |
| post_write_notebook_clean.py | PORT | nbstripout + nbqa wrapper; no identity. |
| precommit_seed_guard.py | PORT | Pre-commit-driven version of the seed guard. |
| precommit_citation_cff.py | PORT | CFF validator; no identity. |

Hooks total: **5 PORT, 3 PARTIAL, 0 LOCAL-ONLY** (of 8).

### Slash commands

| Command | Disposition | Rationale |
|---|---|---|
| adr-new.md | PARTIAL | References missing `adr_TEMPLATE.md` that must move into the bootstrap repo. |
| audit-loop.md | PORT | Trivial body. |
| bootstrap-project.md | PARTIAL | Embeds pseudonym in "canonical layout" label; `--user-email` example carries pseudonym-email; personal dotfiles GitHub URL appears — strip. |
| cite-add.md | PORT | CrossRef-MCP wrapper. |
| commit-with-provenance.md | PARTIAL | Body fail-hard check on publishing-cwd substrings hardcodes a pseudonym fragment — generalize. |
| hypothesis-new.md | PARTIAL | References a personal GitHub URL — generalize. |
| lit-check.md | PORT | Trivial agent-spawn wrapper. |
| preregister.md | PORT | Wrapper around the pre-register-hypothesis skill. |
| render-manuscript.md | PARTIAL | Identity-hygiene paragraph names the pseudonym — strip. |
| reproduce.md | PORT | Trivial agent-spawn wrapper. |

Slash commands total: **5 PORT, 5 PARTIAL, 0 LOCAL-ONLY** (of 10). All
commands must also port to Codex skills (the deprecated `prompts/` is
not recommended) per feature-map item 4.

### Rules

| Rule | Disposition | Rationale |
|---|---|---|
| population-health.md | PORT | Universal reporting-standards + DAG + missing-data policy; cites primary sources only. The cwd-glob list at the top references the maintainer's project directory names — generalize to globs the bootstrap defines. |
| publishing.md | LOCAL-ONLY | Identity-bound: explicitly scoped to a pseudonym; references pseudonym Zenodo, SSRN, personal-site venue, AI-disclosure tied to ICMJE 2026 — keep the methodology content but as a generic publishing rule, not the pseudonym-tied one. |
| quant-project.md | PORT | Universal time-series integrity + HAC + Sharpe-CI methodology; cites primary sources only; cwd-glob list references the maintainer's project directory names — generalize. |

Rules total: **2 PORT (with cwd-glob de-identification), 1 LOCAL-ONLY** (out
of 3).

### Scripts

| File | Disposition | Rationale |
|---|---|---|
| bootstrap_project.py | PARTIAL | Pseudonym in the "canonical layout" label; `~/.claude/cache/` path; cwd-rule resolution targets source-system rule paths — generalize. |
| commit_with_provenance.py | PARTIAL | `~/.claude/cache/` cache-path reference; publishing-cwd substring check references the source-system pseudonym — generalize. |
| render_manuscript.py | PARTIAL | Hardcoded `~/.claude/templates/manuscript/reference.docx` path — rewrite to bootstrap-relative. |
| build_manuscript_reference.py | PARTIAL | Hardcoded `~/.claude/templates/manuscript/reference.docx` output path — rewrite to bootstrap-relative. |
| build_data_manifest.py | PARTIAL | References `~/.claude/templates/data_manifest_schema.json` and `~/.claude/skills/emit-repro-log/assets/emit_repro_log.py` — rewrite to bootstrap-relative. |
| bootstrap_templates/CLAUDE.md.tmpl | PARTIAL | Embeds a personal GitHub URL reference; `~/.claude/CLAUDE.md` inheritance — generalize. |
| bootstrap_templates/README.md.tmpl | PARTIAL | "Dotfiles HEAD" status row references the source customization concept — relabel. |
| bootstrap_templates/pyproject.toml.tmpl | PORT | `<<AUTHOR>>` placeholder; no identity-bound content. |
| bootstrap_templates/.gitignore.tmpl | PORT | Standard secrets + Python + notebook ignores; no identity. |
| bootstrap_templates/.pre-commit-config.yaml.tmpl | PARTIAL | Hook paths under `~/.claude/hooks/` and `~/.claude/scripts/` — rewrite to bootstrap-relative. |
| bootstrap_templates/CHANGELOG.md.tmpl | PORT | Keep-a-Changelog 1.1.0 + SemVer 2.0.0 skeleton; no identity. |
| bootstrap_templates/LICENSE.tmpl | PORT | `<<AUTHOR>>` / `<<YEAR>>` placeholders; no identity. |
| bootstrap_templates/.gitattributes.tmpl | PORT | Text/binary classification + nbstripout filter; no identity. |
| bootstrap_templates/hypothesis_backlog.md.tmpl | PARTIAL | References a source-system internal-library convention name and a personal GitHub URL — strip. |
| bootstrap_templates/protocol_v0.md.tmpl | PORT | Generic study-protocol skeleton; placeholder fields only. |
| bootstrap_templates/manuscript.md.tmpl | PARTIAL | Hardcoded pseudonym in the `Author:` field — replace with placeholder. |
| bootstrap_templates/ai_assistance_statement.md.tmpl | PARTIAL | References the pseudonym project's publishing-rule URL via a personal GitHub link — strip. |

Scripts total: **6 PORT, 11 PARTIAL, 0 LOCAL-ONLY** (of 17).

### Templates

| File | Disposition | Rationale |
|---|---|---|
| CITATION.cff.tmpl | PARTIAL | Hardcoded pseudonym in `authors:` block; references the pseudonym publishing-rule policy — replace with `<<AUTHOR>>` placeholder. |
| adr_TEMPLATE.md | PORT | Generic ADR skeleton; `<<NNNN>>` / `<<TITLE>>` placeholders only. |
| data_manifest_schema.json | PARTIAL | `$id` URL references a personal GitHub dotfiles repo — replace with bootstrap repo URL or relative `$id`. |
| dag_TEMPLATE.dag | PORT | Generic dagitty skeleton citing Textor 2016 IJE; no identity. |
| multipletest_family_TEMPLATE.yaml | PORT | Generic register skeleton citing Hansen 2005 / Davison-Hinkley 1997 / Efron-Tibshirani 1993; no identity. |
| compliance/dua_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in the `recipient:` field and an explanatory annotation — replace with `<<RECIPIENT>>` placeholder. |
| manuscript/reference.docx | PORT | Binary pandoc reference document — generic B&W styling; no identity. |
| manuscript/manuscript_strobe_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in `author:` frontmatter — replace with placeholder. |
| manuscript/manuscript_consort_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in `author:` frontmatter — replace with placeholder. |
| manuscript/manuscript_stard_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in `author:` frontmatter — replace with placeholder. |
| manuscript/manuscript_tripod_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in `author:` frontmatter — replace with placeholder. |
| manuscript/manuscript_prisma_TEMPLATE.md | PARTIAL | Hardcoded pseudonym in `author:` frontmatter — replace with placeholder. |

Templates total: **4 PORT, 8 PARTIAL, 0 LOCAL-ONLY** (of 12).

### Settings + MCP

| File | Disposition | Rationale |
|---|---|---|
| settings.json | PARTIAL | Schema is the source-system JSON, not the Codex TOML; structurally must be rewritten as `config.toml`. The `permissions.allow/deny/ask` Bash patterns are PORT-quality; the hook wiring needs both path generalization and event renaming (`SessionEnd` → `Stop`); the `effortLevel` key has no obvious Codex analog. |
| settings.local.json | LOCAL-ONLY | One-line user-local override; not for the public bootstrap. |
| mcp.json | PARTIAL | Two server entries are PORT-quality (arxiv, crossref both reference public packages and env-var tokens); structure must convert to Codex's `[mcp_servers.<name>]` TOML tables. Disabled-servers commentary (zenodo, zotero) is content the colleague clone can keep as documentation. |
| CLAUDE.md (analog) | LOCAL-ONLY | Identity-bound: pseudonym, role, real-name email, professional background. Do not port the body; write a fresh AGENTS.md instead. |

## Resolution of the shared-SKILL.md question

**Recommendation: option (c) — single shared base with no Codex-specific
overrides needed, save for trivial token replacement.** Evidence below.

### Audit of Claude-specific references across all 14 SKILL.md files

The 14 SKILL.md files cover the full skill catalog (no sampling needed
at N=14). Grep results across the catalog:

- **TRULY-CLAUDE-SPECIFIC tool references**: 1 hit total. The single
  occurrence is in `audit-remediate-loop/SKILL.md` line 32, naming the
  `Agent` tool as the spawn mechanism for parallel auditors. This
  reference is the only Claude-specific tool literal in the entire
  catalog.
- **SHARED tool references** (Read, Edit, Write, Glob, Grep, Bash,
  WebFetch, WebSearch, NotebookEdit): 14 occurrences across 8 files,
  almost all in the subagent frontmatter — these names are identical in
  Codex CLI's subagent schema and need no change.
- **TOOL-AGNOSTIC references**: 49 occurrences across 16 files
  (including assets). These are slash-command literals (e.g.,
  `/audit-loop`, `/cite-add`, `/preregister`, `/commit-with-provenance`),
  not tool names. Slash commands map directly to Codex's
  `/skills:name` invocation pattern (or a hand-renamed equivalent) and
  carry no Claude-specific semantics.
- **Model-name references**: 1 occurrence (`Claude-3.5-Sonnet 4.6%` as
  a SciCode benchmark citation in `audit-remediate-loop/SKILL.md`).
  This is a published-evidence reference, not a tool dependency; can
  remain or be neutralized to "a frontier model."
- **mcp__ccd / TodoWrite / Subagent / Skill tool**: 0 occurrences.
- **Spawning idiom**: 5 mentions of "spawn specialist auditors" /
  "parallel `Agent` calls" / "spawn the literature-check agent". The
  Codex equivalent (subagent invocation via the agent thread mechanism)
  reads identically once `Agent` is reworded to "subagent invocation"
  or the Codex CLI semantic equivalent.

### Rewrite share

- 1 of 14 SKILL.md files (7.1%) needs a 2-line edit to neutralize the
  one `Agent` tool literal.
- 0 of 14 SKILL.md files (0%) reference Claude-specific tool names that
  do not exist in Codex (TodoWrite, mcp__ccd_session__*, etc.).
- 4 of 14 SKILL.md files (28.6%) contain identity references —
  specifically: `deliver-results` (a pseudonym in an asset stylesheet
  name and several references), `emit-repro-log` (a personal GitHub
  username in the schema-issue link), `pit-canary` (a source-system
  internal-library name), and `pre-register-hypothesis` (an `owner:`
  frontmatter default and a pseudonymized upstream template reference)
  — these need to be stripped regardless of whether one tree or two are
  maintained.

### Why option (c), not (a) or (b)

- **Option (a) — strict single shared tree.** Possible in principle:
  the only blocker is the single `Agent` tool literal in
  `audit-remediate-loop/SKILL.md`. A two-word edit ("Agent" →
  "subagent") makes the file dual-target.
- **Option (b) — two separate trees.** Wasteful: 13 of 14 files are
  identical between targets and 1 file needs a trivial token swap.
  Maintaining duplicates doubles edit cost and invites drift.
- **Option (c) — single shared base with optional overrides.**
  Recommended. In practice the single tree IS the base, with one file
  needing a trivial token swap that is harmless in both targets. The
  "overrides" infrastructure is not needed unless the catalog grows
  features that genuinely diverge across the two CLIs.

### Estimated porting effort for SKILL.md content

- Token-replacement edits (e.g., `Agent` → `subagent invocation`):
  ~5 minutes across the catalog.
- Identity-strip edits (4 SKILL.md files containing a pseudonym or
  internal-library reference): ~30 minutes — these are required
  regardless of single vs split tree.
- No structural rewrites required for the body of any SKILL.md.

Frontmatter is shared between Claude Code and Codex CLI (both accept
YAML `name` + `description`), so no frontmatter conversion is needed for
skills.

## Blockers to port

These will fail or misbehave if ported verbatim; each must be
remediated before the bootstrap is functional. They split into four
buckets:

**(a) Schema conversion.**
- `settings.json` → Codex TOML `config.toml`.
- Subagent markdown frontmatter → Codex TOML
  (`name`, `description`, `developer_instructions`, optional `model`,
  `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`).
- `mcp.json` JSON entries → `[mcp_servers.<name>]` TOML tables. Both
  the `arxiv` and `crossref` servers reference public packages and
  env-var tokens — no embedded credentials.

**(b) Event-semantic mismatch.**
- `session_end_audit_log.py` targets a `SessionEnd` event that does
  not exist in Codex CLI. The closest analog `Stop` fires per turn; a
  naive port either spams the audit trail every turn or skips it
  entirely. Mitigation: emit once per turn into a rolling file with
  debounce, or externalize aggregation per the feature map.

**(c) Cross-tree dependencies (port required).**
- Several slash commands reference scripts that live under
  `~/.claude/scripts/` (`bootstrap_project.py`,
  `commit_with_provenance.py`, `render_manuscript.py`,
  `build_manuscript_reference.py`, `build_data_manifest.py`) and
  templates that live under `~/.claude/templates/`
  (`adr_TEMPLATE.md`, `CITATION.cff.tmpl`,
  `multipletest_family_TEMPLATE.yaml`, `hypothesis_backlog.md.tmpl`
  under `scripts/bootstrap_templates/`, five
  `manuscript_*_TEMPLATE.md` files, `reference.docx`). They live under
  `~/.claude/scripts/` and `~/.claude/templates/`; the bootstrap repo
  must port them per the ADR's self-containment principle so a colleague
  clone has all dependencies inside the repository.
- The CITATION.cff pre-commit hook's substitution logic depends on
  `CITATION.cff.tmpl`, which lives under `~/.claude/templates/` and
  also requires port.

**(d) De-identification.**
- `settings.json::hooks` paths hardcode the source-system home
  directory in every entry. Required fix: rewrite to
  `${CODEX_HOME}/hooks/<name>.py` or repository-relative paths;
  cross-platform path handling required.
- The top-level instruction document is identity-bound (pseudonym,
  role, email, venues). The bootstrap must ship a freshly-written
  `AGENTS.md` rather than port it.
- Cwd-glob lists in three rule files and two hooks reference the
  maintainer's specific project directory names — generalize.
- One asset file (matplotlib style sheet) is named with the pseudonym
  and loaded by name from multiple call sites — rename + update
  loaders.
- One asset file and several SKILL.md "References" sections cite a
  personal GitHub username and a pseudonymized internal-library import
  path — strip or genericize.
- The `owner:` frontmatter default in one skill embeds a pseudonym
  substring — drop the default or set to `<TODO: project owner>`.

None are insurmountable. The ADR's self-contained scope requires
fixing all of them inside the new repo rather than referencing the
source customization root.

## Recommendations

1. **Port order, dependency-respecting.** (1) `emit-repro-log` skill;
   (2) six auditor subagents (quant-auditor, epi-auditor,
   literature-check, reproducibility-verifier, code-reviewer,
   format-auditor) converted to Codex TOML; (3) `audit-remediate-loop`
   skill; (4) universal-methodology skills (statistical-analysis,
   validate-data, survival-analysis, mediation-analysis, meta-analysis,
   multiple-imputation, power-analysis, bayesian-workflow, pit-canary,
   multipletest-gate, pre-register-hypothesis); (5) `deliver-results`;
   (6) slash commands ported to Codex skills (not deprecated
   `prompts/`); (7) hooks (path rewrite + SessionEnd → Stop adapter);
   (8) settings (JSON → TOML); (9) MCP (JSON → TOML); (10) rules
   inlined into top-level AGENTS.md or placed as per-subdirectory
   AGENTS.md per the feature map's option (b).

2. **De-identification pass before commit.** Each PARTIAL artifact
   must be scrubbed of pseudonyms, OS usernames, hardcoded source-system
   paths, and personal GitHub URLs before entering the repo. Enforce
   going forward via a repository pre-commit hook.

3. **Skill files: single shared tree.** Maintain SKILL.md files in a
   single canonical location. Token-swap the one `Agent` literal in
   `audit-remediate-loop`. Identity-strip the 4 SKILL.md files that
   mention the pseudonym or the internal source library.

4. **External scripts and templates.** Recreate inside the bootstrap
   repo per the ADR's self-containment principle; do not reference
   the source customization root.

5. **SessionEnd / Stop semantics.** Implement as: emit per-turn into a
   rolling daily file with deduplication on session_id, OR add an
   external timer that aggregates and rotates once per actual session
   close. The latter is more faithful to the original semantics but
   adds a dependency.

6. **MCP servers.** Port both `arxiv` and `crossref` entries as is,
   converting JSON to TOML. Keep the disabled-server commentary as
   inline documentation.

7. **Cwd-glob generalization.** Rule files and hooks reference specific
   personal project directory names — replace with generic globs the
   bootstrap consumer will override.

8. **`Agent` reference in `audit-remediate-loop`.** Reword to "Spawn
   all relevant auditors via subagent invocation in a single message
   so they run concurrently" — valid wording in both CLIs.

9. **Out-of-scope acknowledgments.** Top-level instruction file body,
   `publishing.md` rule body, and `settings.local.json` are
   identity-bound — stay LOCAL-ONLY, not in the bootstrap.

## References

- [docs/SCOPE.md](../SCOPE.md) — repository scope and de-identification
  commitment.
- [docs/decisions/0001-repo-scope-and-naming.md](../decisions/0001-repo-scope-and-naming.md)
  — ADR mandating self-containment and de-identified content.
- [docs/research/codex_feature_map_2026-05-18.md](codex_feature_map_2026-05-18.md)
  — Codex CLI surface-by-surface map; high-friction items 1-6.
- [Codex CLI documentation](https://developers.openai.com/codex/) —
  the authoritative source for Codex CLI subagent, skill, hook, and
  config schemas.
- ICMJE Recommendations, January 2026 update — AI-assistance disclosure
  requirements.
- Wang et al. (2024) "Mixture of Agents" arXiv:2406.04692; Du et al.
  (2023) arXiv:2305.14325 — multi-agent debate / parallel-specialist
  ensembles cited by the audit-remediate-loop skill.
