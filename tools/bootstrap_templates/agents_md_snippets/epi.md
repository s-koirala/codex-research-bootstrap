# Population-health rules

This snippet is installed as a per-subdirectory `AGENTS.md` (or appended to
the project root `AGENTS.md`) by `tools/bootstrap_project.py --kind epi`.
Codex walks from the git root to the current working directory and
concatenates each `AGENTS.md` it encounters, so this content activates by
path: it applies whenever Codex is operating inside a project whose cwd
matches one of the globs below.

**Apply when cwd matches any of:** `**/epidemiolog*/`, `**/clinical*/`,
`**/cohort*/`, `**/case-control*/`, `**/RCT*/`, `**/diagnostic*/`,
`**/population-health*/`.

If cwd does not match, ignore this section entirely.

## Reporting standards

Declared at the top of the analysis document:

- **STROBE** — observational studies.
- **CONSORT** — randomized controlled trials.
- **STARD** — diagnostic-accuracy studies.
- **TRIPOD** — prediction models.
- **PRISMA** — systematic reviews and meta-analyses.

State which standard applies before any analysis prose, and follow its
checklist for every required item.

## Confounding and causal inference

- **Declare the DAG first.** Use dagitty or plain text; the DAG must precede
  adjustment-set selection. The bootstrap ships
  `templates/dag_TEMPLATE.dag` for the dagitty form.
- **Adjustment-set selection via the back-door criterion** (Pearl), not a
  kitchen-sink regression. The DAG identifies the minimal sufficient
  adjustment set; the regression specifies only those covariates.
- **Sensitivity to unmeasured confounding.** Report the E-value for each
  primary causal estimate per
  [VanderWeele & Ding 2017, Ann Intern Med 167:268, DOI 10.7326/M16-2607](https://doi.org/10.7326/M16-2607).

## Missingness

- **Declare the MCAR / MAR / MNAR assumption** with supporting evidence
  (e.g., logistic regression of missingness on observed covariates;
  Little's MCAR test) before choosing a handling strategy.
- **Primary analysis: multiple imputation by chained equations (MICE)**
  with `m` greater than or equal to the percentage of incomplete cases per
  [White, Royston, Wood 2011, Stat Med 30:377, DOI 10.1002/sim.4067](https://doi.org/10.1002/sim.4067),
  unless an MCAR assumption is supported by the evidence above.
- **Complete-case analysis as sensitivity only**, never as the primary
  analysis under MAR.

## Ethics and compliance

- **Protected health information (PHI) must not leave the project's data
  directory.** No PHI in committed files, repository issues, or transcript
  logs. The `hooks/pre_write_phi_guard.py` hook flags common PHI patterns
  on writes inside epi cwds; it is a backstop, not a substitute for
  reviewer attention.
- **IRB and dataset-use-agreement (DUA) constraints are documented at the
  project root.** The bootstrap ships
  `templates/compliance/dua_TEMPLATE.md` as a starting point.
