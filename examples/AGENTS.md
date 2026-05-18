# AGENTS.md (sample)

This is a bootstrap-supplied sample for your `~/.codex/AGENTS.md`. Copy it
verbatim into that path, or merge its body into a file you already maintain
there. Anything you write **above** the `AUDIT-LOOP:AGENTS:START` marker or
**below** the `AUDIT-LOOP:AGENTS:END` marker is your own prose and will be
preserved when the bootstrap's installer refreshes the managed section in a
future update; anything between the markers is bootstrap-managed and will be
overwritten on refresh.

<!-- AUDIT-LOOP:AGENTS:START -->

## Quality posture: audit-remediate-loop

Every non-trivial deliverable produced in any of your research projects
passes through an **audit-remediate-loop** with six-branch parallel specialist
auditors and a three-round remediation cap:

- **reproducibility-verifier** — pinned dependencies, seeds, dataset
  checksums, runnable entrypoint, ReproLog envelope.
- **code-reviewer** — idiom, style, error handling, type hints, docstring
  completeness.
- **quant-auditor** — statistical method fidelity and numerical correctness
  for quantitative research projects.
- **epi-auditor** — DAG declaration, back-door adjustment-set selection,
  E-value sensitivity, and reporting-standard coverage for epidemiology and
  population-health projects.
- **format-auditor** — magic-number policy, template-substitution
  completeness, citation-format consistency, docstring style.
- **literature-check** — citation verification against primary sources.

The quant-auditor and epi-auditor are mutually exclusive at the calculations
branch: which one engages is determined by cwd-glob dispatch against your
project's path. The other four branches always run.

Three-round cap. Multi-agent self-consistency gains taper at moderate sample
counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751)); three rounds
balance coverage against cost. Structured JSON findings; diff-based
remediation; re-audit each round.

Invoke the loop explicitly via the `/audit-loop` slash command after writing
a draft, or implicitly via the `audit-remediate-loop` skill (description
matches when Codex sees a non-trivial deliverable in your transcript).

## De-identification posture

The bootstrap is distributed to research colleagues, so its source tree is
de-identified. **Your** own `~/.codex/AGENTS.md`, your projects, and your
working tree are not bound by the bootstrap's de-identification commitment
— you decide what identifying information is appropriate for your context
and threat model.

If you want to enforce identity-hygiene on your own commits (recommended
for any artifact you intend to share, publish, or open-source), the
bootstrap ships `tools/check_identity.py`. Add your own forbidden-token
list at `tools/check_identity_tokens.local.txt` (one token per line). The
`.local.txt` extension is gitignored so your local-only list does not ship
upstream. Wire the scanner as a pre-commit hook in your project to block
leaks before they reach git history.

## Methodology mandates

The following rules apply to research artifacts authored in your own
projects. The bootstrap inlines them here so any project clone has the
guidance available without consulting an external rules file.

### Quantitative research projects

Glob match: any project whose path matches `**/*backtest*/`,
`**/*factor*/`, `**/*signal*/`, or `**/*strategy*/`.

- **No look-ahead.** Every feature must be computable at time t using only
  data available at time t. Train, validation, and test splits are
  time-ordered and disjoint; walk-forward cross-validation only, never
  k-fold for time-series data.
- **Returns.** State log vs. arithmetic and the compounding convention at
  the top of the analysis. Adjust prices for corporate actions before any
  return calculation.
- **Standard errors.** Newey-West (HAC) with data-dependent bandwidth
  ([Newey & West 1994, DOI 10.2307/2297912](https://doi.org/10.2307/2297912))
  or Andrews parametric plug-in
  ([Andrews 1991, DOI 10.2307/2938229](https://doi.org/10.2307/2938229)).
- **Sharpe confidence intervals.** Single-strategy via
  [Opdyke 2007 DOI 10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084).
  Pairwise comparison via studentized time-series bootstrap
  ([Ledoit & Wolf 2008 DOI 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002)).
- **Multiple testing across strategies.** White's reality check
  ([White 2000 DOI 10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152))
  or Hansen's SPA
  ([Hansen 2005 DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063)).
- **Reporting.** Universe, rebalance frequency, transaction-cost model,
  survivorship-bias treatment, data vendor + snapshot date. Performance
  metrics: Sharpe, Sortino, max drawdown, turnover, capacity estimate.
- **Citations.** Every factor, signal, or rule must have a citation or a
  derivation. No unattributed folklore factors.

### Epidemiology and population-health projects

Glob match: any project whose path matches `**/epidemiolog*/`,
`**/clinical*/`, `**/cohort*/`, `**/case-control*/`, `**/RCT*/`, or
`**/diagnostic*/`.

- **Reporting standard.** Declared at the top of each analysis document:
  STROBE (observational), CONSORT (randomized controlled trial), STARD
  (diagnostic accuracy), TRIPOD (prediction model), PRISMA (systematic
  review / meta-analysis).
- **DAG before adjustment.** Declare a directed acyclic graph (dagitty or
  plain text) before choosing your adjustment set. Pick the adjustment set
  via the back-door criterion (Pearl), not a kitchen-sink regression.
- **Sensitivity.** Report the E-value
  ([VanderWeele & Ding 2017, Ann Intern Med 167:268, DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607))
  for each primary causal estimate.
- **Missingness.** Declare the MCAR / MAR / MNAR assumption with evidence.
  Primary analysis: multiple imputation with m ≥ percentage of incomplete
  cases ([White, Royston, Wood 2011, Stat Med 30:377, DOI 10.1002/sim.4067](https://doi.org/10.1002/sim.4067))
  unless MCAR is supported by the evidence. Complete-case analysis as a
  sensitivity check only.
- **PHI.** Protected health information must not leave the project's data
  directory. Document any IRB or dataset-use-agreement constraints at the
  project root.

### Publishing and manuscript work

Any project authoring a manuscript, supplementary materials, or a
submission package:

- Include an AI-assistance statement in the manuscript appendix or the
  project README listing the models used (with version), the role they
  played (idea, code, prose, audit), and the path to your reproducibility
  log.
- Follow the [ICMJE Recommendations (updated January 2026)](https://www.icmje.org/recommendations/).
  AI cannot be a co-author of a deliverable. AI assistance must be
  disclosed.

## Stop-event audit-trail aggregation

Codex CLI has no `SessionEnd` event; the `Stop` event fires once per turn
rather than once per session. The bootstrap's hooks handle this asymmetry
for you:

- Every `Stop` event appends a per-turn JSON record to
  `logs/turn_<session_id>_<n>.json` in your project.
- The next `SessionStart` aggregates closed-session turn files into
  `docs/audits/session_trail_<date>_<session_id>.md` and removes the
  per-turn files for the now-closed session.
- A manual `/audit-flush` slash command exists if you want to force the
  aggregation before closing a session intentionally.

The closed-session detection treats any session whose turn-file mtime
predates the new SessionStart by the configured idle window as closed; the
aggregator runs idempotently on each SessionStart.

## Reproducibility envelope (ReproLog)

Every bootstrap, backtest, or inference run emits a JSON ReproLog record to
`logs/reprolog/<run-id>.json` capturing: git HEAD, `pip freeze` SHA-256,
dataset checksum(s), RNG seed, model commit hash, Python version, platform,
container digest (if any), and OS release. The ReproLog path is threaded
into commit messages via the `commit-with-provenance` skill's trailers.

<!-- AUDIT-LOOP:AGENTS:END -->

## References

The bootstrap installs its operational surfaces under your `$CODEX_HOME`
(default `~/.codex/`):

- `~/.codex/skills/` — bootstrap-installed skills (methodology, audit,
  delivery). Browse via `/skills` in the Codex CLI.
- `~/.codex/agents/` — TOML subagent definitions (six auditors plus
  supporting specialists). Browse via `/agents`.
- `~/.codex/templates/` — manuscript, ADR, DAG, multiple-testing family,
  and compliance templates. Used by `bootstrap-project`, `adr-new`,
  `render-manuscript`, and related skills.
- `~/.codex/hooks.json` — event wiring for `SessionStart`, `Stop`, and the
  pre-commit-style guards.

For installer updates and the canonical project description, refer back to
the [bootstrap repository README](https://github.com/) (substitute your
clone's remote URL). Re-run the installer after `git pull` to refresh the
bootstrap-managed surfaces; the AGENTS.md sample is not auto-applied — you
re-merge it yourself when the upstream sample changes.
