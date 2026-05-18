# Installing `codex-research-bootstrap` → `$CODEX_HOME`

User-level OpenAI Codex CLI configuration for research workflows in statistics,
population science and public health, quantitative research, results
compilation, and manuscript drafting. The bootstrap installs a curated surface
into `$CODEX_HOME` (default `~/.codex/`) and activates an audit-remediate-loop
quality-control pattern over every non-trivial deliverable produced in any
project that uses it.

Deploys 24 skills, 7 subagents, 8 lifecycle hooks (6 event-wired plus 2
pre-commit-framework hooks) and a shared helper module, 12 templates, plus the
[hooks.json](.codex/hooks.json) event-wiring manifest and a project-level
[config.toml](.codex/config.toml) (permissions, subagent caps, two MCP servers:
arxiv and crossref). Installer is stdlib-only Python; idempotent via SHA-256
content-hash skip; differing files are backed up to
`<target>/.bootstrap-backups/<timestamp>/` before overwrite.

## How to use this guide

- **Manual install** (3 lines): jump to [§Quickstart — manual](#quickstart--manual-no-ai).
- **AI-assisted install**: jump to [§Quickstart — AI-assisted](#quickstart--ai-assisted). A capable tool-using agent can install from the bare repo URL; the supported path is the structured prompt in the `<details>` block of that section. Inside that block is one fenced code block — **copy the contents of that code block (and only that block) into a fresh agent session**. The rest of this INSTALL.md is documentation; do not paste it.
- **Verification, AGENTS.md activation, inventory, MCP servers, updates, identity hygiene**: continue past the quickstart sections.

## Requirements

Three tiers. The installer detects what is present and reports what is missing.

| Tier | Tool | Purpose | Install hint |
|---|---|---|---|
| Required | `git` | repository operations, provenance trailers, identity-hygiene gate | system package manager |
| Required | OpenAI Codex CLI (`codex`) | runtime this bootstrap targets | `npm i -g @openai/codex` or `brew install --cask codex` ([developers.openai.com/codex/cli](https://developers.openai.com/codex/cli); Homebrew cask listing at [formulae.brew.sh/cask/codex](https://formulae.brew.sh/cask/codex)) |
| Required | Python ≥ 3.10 | installer, identity-hygiene scanner, hooks, verification snippets | [python.org](https://www.python.org/) |
| Detected-recommended | `uv` | env manager; needed by the bundled MCP servers (arxiv, crossref) and several skill assets | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Detected-optional | `pandoc` | Markdown → DOCX rendering for the `render-manuscript` skill | `choco install pandoc` (Windows) / `brew install pandoc` (macOS) / `apt install pandoc` (Linux) |
| Detected-optional | `ruff` | Python lint/format used by `code-reviewer` audits | `pip install ruff` or via `uv tool install ruff` |
| Detected-optional | `nbstripout` | notebook-metadata stripper used by `post_write_notebook_clean` and the project's pre-commit gate | `pip install nbstripout` |

**Cross-platform note.** Manual install is supported natively on Windows via
[install.ps1](install.ps1) (PowerShell 5.1 compatible); macOS and Linux via
[install.sh](install.sh). Both are thin wrappers around [tools/install.py](tools/install.py),
which is the source of truth — invoke `python tools/install.py --help` for the
full flag list. The AI-assisted prompt body in
[§Quickstart — AI-assisted](#quickstart--ai-assisted) is POSIX shell
(bash / zsh); Windows users either run the prompt under Git Bash or WSL, or
follow the manual quickstart and use the verification snippets in
[§Verification](#verification-after-install) (POSIX and PowerShell variants
provided).

## Quickstart — manual (no AI)

POSIX (macOS / Linux / Git Bash / WSL):

```bash
git clone https://github.com/s-koirala/codex-research-bootstrap.git
cd codex-research-bootstrap
./install.sh --dry-run        # preview, no writes
./install.sh                  # safe deploy; backs up differing files
# If $CODEX_HOME already exists from prior Codex use, the installer exits 6 to
# protect your prior content. Re-run with --force to back-up-then-replace:
# ./install.sh --force
```

PowerShell (Windows):

```powershell
git clone https://github.com/s-koirala/codex-research-bootstrap.git
cd codex-research-bootstrap
.\install.ps1 --dry-run       # preview, no writes
.\install.ps1                 # safe deploy; backs up differing files
# Pre-existing $env:CODEX_HOME: re-run with --force to back-up-then-replace.
```

Safe to re-run. The installer is idempotent: each file is content-hashed and
skipped when identical; differing files are moved to
`$CODEX_HOME/.bootstrap-backups/<UTC-timestamp>/` before overwrite. The set of
tracked files is recorded in `$CODEX_HOME/.bootstrap-manifest.json` (schema
`codex-research-bootstrap.manifest/v1`). The installer refuses to write into an
existing non-empty `$CODEX_HOME` that lacks a bootstrap manifest unless
`--force` is passed — your prior content is preserved this way.

**One follow-up is manual:** the installer does not touch
`$CODEX_HOME/AGENTS.md`. Activate the bootstrap's quality-posture content by
copying or merging [examples/AGENTS.md](examples/AGENTS.md) yourself; see
[§Activate AGENTS.md](#activate-agentsmd) below.

## Quickstart — AI-assisted

**URL-only path (capable agents).** Paste a single line into a fresh agent
session and let it figure out the rest:

```text
Install https://github.com/s-koirala/codex-research-bootstrap.git into my Codex
CLI configuration, then verify and audit the install per its INSTALL.md.
```

A capable tool-using agent (Codex CLI, Claude Code, or any framework with
shell + file tools) will fetch the repo, read [INSTALL.md](INSTALL.md), and
follow the manual quickstart plus verification steps below. The URL-only path
is acceptable for one-shot installs; it is not the supported path — behavior
across agents and model versions varies.

**Structured-prompt path (supported).** Copy *only* the contents of the fenced
code block inside the `<details>` element below (not this paragraph, not the
`<details>` markers, not anything outside the triple backticks) into a fresh
agent session. The block is self-contained: the agent reads it as a single
instruction set and executes the 3-stage install + verify + audit protocol
under the bootstrap's six-branch audit-remediate-loop (four branches engage
for a config install; the calculations branch quant-auditor / epi-auditor
stands down on non-analytical artifacts).

<details>
<summary>Click to expand the directive — paste contents of the inner code block only</summary>

```text
# ════════ BEGIN PASTE ════════
You are bootstrapping codex-research-bootstrap on this machine. Execute every
step via the shell, file-read, and subagent tools available to your runtime
(Codex CLI, Claude Code, or equivalent). Do NOT simulate — actually run each
command, capture output, halt on any unexpected failure. Cap audit-remediate
at 3 rounds per the bootstrap's audit-remediate-loop skill.

Shell conventions: POSIX (bash / zsh). On Windows, run under Git Bash or WSL.
Treat REPO and TARGET below as values to substitute into each subsequent
command; do NOT rely on shell-variable persistence across tool calls if your
runtime runs each command in a fresh subprocess — re-set the values at the
start of each step or inline them literally.

REPO=https://github.com/s-koirala/codex-research-bootstrap.git
TARGET="${CODEX_HOME:-$HOME/.codex}"

# Stage 1 — install
1. Pre-flight: `git --version`; `python --version` (>= 3.10); `codex --version`
   (install via `npm i -g @openai/codex` or `brew install --cask codex` if
   missing). Halt on any required-tier failure.
2. Clone or fast-forward. Use `git -C` so no `cd` is needed (each command is
   self-contained; safe under fresh-subprocess agent runtimes). If the dirty
   check echoes `HALT`, stop and surface to the user:

   BOOT="$HOME/codex-research-bootstrap"
   if [ ! -d "$BOOT/.git" ]; then
     git clone "$REPO" "$BOOT"
   elif [ -n "$(git -C "$BOOT" status --porcelain)" ]; then
     echo "HALT: dirty working tree in $BOOT"
   else
     git -C "$BOOT" pull --ff-only
   fi

3. Preview: `python "$HOME/codex-research-bootstrap/tools/install.py" --dry-run`.
   Capture the action list. If any path looks unexpected, HALT.
4. Apply: `python "$HOME/codex-research-bootstrap/tools/install.py"`. The
   installer prints per-file actions (install / skip-identical /
   backup+overwrite), writes `$TARGET/.bootstrap-manifest.json`, and refuses to
   write into a non-empty pre-existing $CODEX_HOME without `--force` — preserve
   the user's prior config; surface the warning rather than passing `--force`
   silently.
5. AGENTS.md activation is OPT-IN. Read
   `$HOME/codex-research-bootstrap/examples/AGENTS.md` — it carries
   HTML-comment delimited mutation markers
   `<!-- AUDIT-LOOP:AGENTS:START -->` / `<!-- AUDIT-LOOP:AGENTS:END -->`.
   Propose a copy-or-merge plan into `$TARGET/AGENTS.md`; do NOT write that
   file without the user's confirmation.

# Stage 2 — verify (filesystem + runtime; not self-report)
6. Inventory and manifest cross-check. The canonical file count is the
   `.bootstrap-manifest.json` `files` array length. Python one-liner form
   (avoids heredoc-indent hazards under markdown numbered lists):

   python -c "import json,os; t=os.environ.get('CODEX_HOME') or os.path.expanduser('~/.codex'); m=json.load(open(os.path.join(t,'.bootstrap-manifest.json'))); print('files_tracked:',len(m['files'])); print('bootstrap_git_head:',m['bootstrap_repo_git_head'])"

   Expected on-disk surface: skills/ (24 subdirs, each containing at minimum
   a SKILL.md; three bundle additional assets — deliver-results, emit-repro-log,
   pre-register-hypothesis); agents/ (7 .toml); hooks/ (8 hook scripts plus
   a shared `_common.py` helper = 9 .py files); templates/ (12 files across
   2 subdirs: manuscript/ has 6, compliance/ has 1, root has 5); plus
   `hooks.json` and `config.toml`. `.gitkeep` placeholders do NOT ship
   (excluded by the installer).

7. Smoke-test every hook with empty stdin and confirm exit 0 (fail-open on
   malformed stdin is the per-hook convention, implemented in each hook's
   `main()` — see `hooks/pre_write_seed_guard.py` for the canonical pattern):

   python -c "import os,sys,subprocess,glob; t=os.environ.get('CODEX_HOME') or os.path.expanduser('~/.codex'); hooks=sorted(p for p in glob.glob(os.path.join(t,'hooks','*.py')) if not os.path.basename(p).startswith('_')); [print(subprocess.run([sys.executable,p],input=b'{}',capture_output=True,timeout=10).returncode, p) for p in hooks]"

   Every returncode must be 0.

8. Realistic payload test for pre_write_seed_guard.py. The `tool_name` field
   is included for hook-spec completeness; this hook reads only `tool_input`.
   The `file_path` value is metadata for extension/exclusion checks — the
   hook never opens it, so any synthetic name works cross-platform:

   printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"synthetic-seed-test.py","content":"import numpy as np\nx = np.random.rand(100)"}}' \
     | python "$TARGET/hooks/pre_write_seed_guard.py"

   Stdout must contain a JSON object with `hookSpecificOutput` whose
   `permissionDecision` is `ask` (the unseeded `np.random.rand` call triggers
   the guard).

9. Tool inventory (record presence; do not auto-install): `codex --version`,
   `uv --version`, `ruff --version`, `pytest --version`, `pandoc --version`,
   `nbstripout --version`.
10. MCP-server availability: read `$TARGET/config.toml` `[mcp_servers]`
    section. Two ship by default (`arxiv`, `crossref`), both invoked via
    `uv tool run` (equivalent to `uvx`). If `uv` is absent, flag that
    arxiv/crossref will fail at first use and recommend installing uv.
11. Identity check: report `git config --global user.name`,
    `git config --global user.email`, hostname, and a portable platform
    string:

    python -c "import platform; print(platform.platform())"

    The bootstrap itself is de-identified for distribution; consumer identity
    is consumer-controlled — report, do not enforce.

# Stage 3 — audit (parallel specialist subagents; max 3 rounds)
12. Spawn in parallel (single message, multiple subagent invocations), briefing
    each with the deployed `$TARGET/agents/<name>.toml`:
    - `reproducibility-verifier`: verify `$TARGET` tree matches the source
      repo file-for-file; manifest SHA-256s match; hooks runnable.
    - `code-reviewer`: audit `$TARGET/hooks/*.py` for code quality, type
      hints, cross-platform path handling, fail-open contract.
    - `format-auditor`: verify identity-hygiene (no real-name strings in
      installed surface), magic-numbers compliance, template-substitution
      completeness in templates/.
    - `literature-check`: verify every URL and citation in INSTALL.md and in
      the deployed `$TARGET/agents/*.toml` resolves and matches the cited
      claim.
    The calculations-branch auditor (quant-auditor XOR epi-auditor) is NOT
    spawned for a config install: the artifact is not a statistical analysis.
    Spawn it only when an audit runs inside a downstream research project.
13. Triage: critical blocks; major remediated in-round; minor logged.
    Remediate in-place under `$TARGET` — do NOT modify the upstream
    bootstrap repo (no `git add`, `git commit`, or `git push`).
14. Re-spawn auditors that returned findings; exit when all return `accept`
    or after round 3. Surface any residual to the user.

# Final report
Create the report directory if absent (it is gitignored):
  mkdir -p "$HOME/codex-research-bootstrap/logs"

Write `$HOME/codex-research-bootstrap/logs/install_<hostname>_<YYYY-MM-DD>.md`
(replace any `.` in hostname with `-` for filesystem friendliness) with:
machine info; stage 1/2/3 results; tool inventory; MCP availability; audit
findings + disposition + residual risk; identity check; manual follow-ups
(AGENTS.md activation if declined, pandoc/uv install if absent).

Do NOT `git add`, `git commit`, or `git push`. Install is read-only toward
the upstream repo. Surface the report path to the user.
# ════════ END PASTE ════════
```

</details>

The AI path runs the same [tools/install.py](tools/install.py) commands as the
manual path, plus filesystem and runtime verification, a six-branch
audit-remediate-loop with the calculations branch suppressed for the
config-install artifact (four auditors engage: reproducibility-verifier,
code-reviewer, format-auditor, literature-check), and an installation report.
Stop pasting at the `END PASTE` marker; everything after this point is
documentation for the human.

## Verification (after install)

The canonical file count is the manifest's `files` array length — this
matches across POSIX and PowerShell:

POSIX (bash / zsh):

```bash
CX="${CODEX_HOME:-$HOME/.codex}"
ls "$CX"/{skills,agents,hooks,templates,hooks.json,config.toml}
# Expect: skills/ (24 subdirs), agents/ (7 .toml), hooks/ (9 .py = 8 hooks +
# _common.py helper), templates/ (5 root files + manuscript/ + compliance/),
# plus hooks.json and config.toml. `.gitkeep` placeholders do NOT ship.

python -c "import json,os; t=os.environ.get('CODEX_HOME') or os.path.expanduser('~/.codex'); m=json.load(open(os.path.join(t,'.bootstrap-manifest.json'))); print('files_tracked:', len(m['files'])); print('bootstrap_git_head:', m['bootstrap_repo_git_head'])"
```

PowerShell (5.1+ compatible):

```powershell
$cx = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
Get-ChildItem $cx | Where-Object Name -in skills,agents,hooks,templates,hooks.json,config.toml

python -c "import json,os; m=json.load(open(os.path.join(r'$cx','.bootstrap-manifest.json'))); print('files_tracked:', len(m['files'])); print('bootstrap_git_head:', m['bootstrap_repo_git_head'])"
```

Inside a Codex CLI session, `/skills` should list the 24 installed skills and
`/agents` should list the 7 installed subagents.

## Activate AGENTS.md

The installer does not write `$CODEX_HOME/AGENTS.md` (a Codex CLI session's
top-of-walk policy file). Activate the bootstrap's quality-posture content
yourself:

POSIX:

```bash
CX="${CODEX_HOME:-$HOME/.codex}"
cp examples/AGENTS.md "$CX/AGENTS.md"            # fresh install
# To merge into an existing file you already maintain: preserve anything
# above `<!-- AUDIT-LOOP:AGENTS:START -->` and below
# `<!-- AUDIT-LOOP:AGENTS:END -->`; replace the content between markers.
```

PowerShell:

```powershell
$cx = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
Copy-Item examples\AGENTS.md (Join-Path $cx 'AGENTS.md')
```

The bootstrap-managed block is delimited by HTML-comment markers
`<!-- AUDIT-LOOP:AGENTS:START -->` / `<!-- AUDIT-LOOP:AGENTS:END -->`, so
future installer updates can refresh only the content between them while
preserving any prose you add above or below. Re-run the merge after a
bootstrap `git pull` brings new content into
[examples/AGENTS.md](examples/AGENTS.md).

## Inventory

### Skills (24)

Methodology: [statistical-analysis](skills/statistical-analysis/SKILL.md),
[validate-data](skills/validate-data/SKILL.md),
[power-analysis](skills/power-analysis/SKILL.md),
[bayesian-workflow](skills/bayesian-workflow/SKILL.md),
[survival-analysis](skills/survival-analysis/SKILL.md),
[mediation-analysis](skills/mediation-analysis/SKILL.md),
[meta-analysis](skills/meta-analysis/SKILL.md),
[multiple-imputation](skills/multiple-imputation/SKILL.md),
[multipletest-gate](skills/multipletest-gate/SKILL.md),
[pit-canary](skills/pit-canary/SKILL.md),
[pre-register-hypothesis](skills/pre-register-hypothesis/SKILL.md).

Audit and reproducibility: [audit-remediate-loop](skills/audit-remediate-loop/SKILL.md),
[audit-loop](skills/audit-loop/SKILL.md),
[lit-check](skills/lit-check/SKILL.md),
[reproduce](skills/reproduce/SKILL.md),
[emit-repro-log](skills/emit-repro-log/SKILL.md).

Workflow and delivery: [bootstrap-project](skills/bootstrap-project/SKILL.md),
[hypothesis-new](skills/hypothesis-new/SKILL.md),
[preregister](skills/preregister/SKILL.md),
[adr-new](skills/adr-new/SKILL.md),
[cite-add](skills/cite-add/SKILL.md),
[commit-with-provenance](skills/commit-with-provenance/SKILL.md),
[deliver-results](skills/deliver-results/SKILL.md),
[render-manuscript](skills/render-manuscript/SKILL.md).

### Subagents (7)

[quant-auditor](.codex/agents/quant-auditor.toml),
[epi-auditor](.codex/agents/epi-auditor.toml) (mutually exclusive at the
calculations branch, cwd-glob dispatched),
[literature-check](.codex/agents/literature-check.toml),
[reproducibility-verifier](.codex/agents/reproducibility-verifier.toml),
[code-reviewer](.codex/agents/code-reviewer.toml),
[format-auditor](.codex/agents/format-auditor.toml),
[dag-drafter](.codex/agents/dag-drafter.toml).

### Hooks (8 scripts plus a shared helper)

Event-wired in [.codex/hooks.json](.codex/hooks.json): SessionStart
[session_start_provenance.py](hooks/session_start_provenance.py); Stop
[stop_audit_aggregator.py](hooks/stop_audit_aggregator.py); PreToolUse:Bash
[pre_bash_safety.py](hooks/pre_bash_safety.py); PreToolUse:Write|Edit|MultiEdit|NotebookEdit
[pre_write_seed_guard.py](hooks/pre_write_seed_guard.py) and
[pre_write_phi_guard.py](hooks/pre_write_phi_guard.py); PostToolUse:Write|Edit|NotebookEdit
[post_write_notebook_clean.py](hooks/post_write_notebook_clean.py).

Pre-commit-framework hooks wired in [.pre-commit-config.yaml](.pre-commit-config.yaml):
[precommit_seed_guard.py](hooks/precommit_seed_guard.py),
[precommit_citation_cff.py](hooks/precommit_citation_cff.py).

Shared helper (imported by hooks; not invoked directly):
[hooks/_common.py](hooks/_common.py).

Codex CLI has no `SessionEnd` event; the `Stop` event fires once per turn
([developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks)).
The bootstrap's hooks bridge this asymmetry by appending per-turn JSON
records on `Stop` and aggregating closed-session turn files on the next
`SessionStart` — see [examples/AGENTS.md](examples/AGENTS.md)
"Stop-event audit-trail aggregation" for the full mechanism.

### Templates (12)

Manuscript: five reporting-standard skeletons under
[templates/manuscript/](templates/manuscript/) covering STROBE, CONSORT,
STARD, TRIPOD, PRISMA, plus [reference.docx](templates/manuscript/reference.docx)
for `render-manuscript`.

Project scaffolding: [adr_TEMPLATE.md](templates/adr_TEMPLATE.md),
[dag_TEMPLATE.dag](templates/dag_TEMPLATE.dag),
[multipletest_family_TEMPLATE.yaml](templates/multipletest_family_TEMPLATE.yaml),
[data_manifest_schema.json](templates/data_manifest_schema.json),
[CITATION.cff.tmpl](templates/CITATION.cff.tmpl),
[compliance/dua_TEMPLATE.md](templates/compliance/dua_TEMPLATE.md).

## MCP servers

Two servers are declared in [.codex/config.toml](.codex/config.toml) and ship
to `$CODEX_HOME/config.toml` automatically — there is no separate registration
step:

- **arxiv** — paper search, metadata, citation graphs. Source:
  [github.com/blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server).
  Consumed by `literature-check`.
- **crossref** — DOI → CSL-JSON / BibTeX / RIS resolution. Source:
  [github.com/h-lu/crossref-cite-mcp](https://github.com/h-lu/crossref-cite-mcp).
  Consumed by `cite-add`. Set `CROSSREF_MAILTO` in your shell env for
  CrossRef's polite-pool rate limits.

Both invoke via `uv tool run` (equivalent to `uvx`; see
[uv tools docs](https://docs.astral.sh/uv/concepts/tools/)). The consumer does
not pre-install the underlying Python packages — `uv` resolves and caches each
server on first invocation. If `uv` is absent, the installer's pre-flight
prints an install hint and the servers will fail at first use; install `uv`
then.

## Updates

```bash
cd codex-research-bootstrap
git pull --ff-only
./install.sh          # or .\install.ps1
```

The installer is idempotent: unchanged files are skipped; changed files
trigger a backup-then-replace. The AGENTS.md sample is not auto-applied —
re-run the merge described in [§Activate AGENTS.md](#activate-agentsmd) when
the upstream sample changes.

## Identity hygiene

The bootstrap is distributed for local clone by research colleagues. Its
source tree is de-identified per [docs/SCOPE.md](docs/SCOPE.md)
"De-identification commitment" — no real names, pseudonyms tied to a single
individual, personal email addresses, OS usernames, workstation identifiers,
or institutional affiliations beyond those necessary for citation of external
work. Contributors are expected to maintain this commitment in any pull
request or fork that re-merges upstream.

Your **own** `$CODEX_HOME/AGENTS.md`, your projects, and your working tree are
not bound by the bootstrap's de-identification commitment — you decide what
identifying information is appropriate for your context. If you want to
enforce identity hygiene on your own commits (recommended for any artifact
you intend to share, publish, or open-source), the bootstrap ships
[tools/check_identity.py](tools/check_identity.py). Add your own
forbidden-token list at `tools/check_identity_tokens.local.txt` (one token per
line; the `.local.txt` suffix is gitignored). Wire the scanner as a pre-commit
hook in your project to block leaks before they reach git history.

For **contributors** to this bootstrap, the pre-commit gate is mandatory:

```bash
pip install pre-commit
pre-commit install
```

The gate runs the identity scanner against staged files and blocks any commit
that contains a forbidden token.

## AI-assistance statement

This INSTALL.md was AI-drafted (model `claude-opus-4-7`, roles `idea`, `prose`,
`audit`) and passed through the bootstrap's own audit-remediate-loop with the
four branches applicable to a config-install artifact (reproducibility-verifier,
code-reviewer, format-auditor, literature-check; the calculations-branch
auditor stood down). Audit trail: [docs/audits/](docs/audits/). Per the
[ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/)
— specifically the
[Defining the Role of Authors and Contributors](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html)
guidance — AI is acknowledged as a tool, not an author; AI assistance is
disclosed.

## License

MIT — see [LICENSE](LICENSE).
