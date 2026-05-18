---
name: {HID} — {TITLE}
description: Pre-registered design doc for hypothesis {HID}
type: project
hypothesis_id: {HID}
tier: {TIER}
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: <TODO: project owner>
created: {DATE}
citations: {CITATIONS}
external_doi: <<EXTERNAL_DOI>>  # set on optional OSF upload; null/omit for internal-only
---

# {HID} — {TITLE}

This document is the pre-registration record for hypothesis {HID}. It is frozen at
`designed` status; any change after that point requires a new hypothesis ID.

The 11 sections below are a generic quant-research pre-registration skeleton. Inline
commentary cites the conceptual anchor that governs the content of each section.

## 1. Hypothesis

State the null H0 and alternative H1 in precise form (sign and magnitude of the test
statistic, not prose). Identify the economic mechanism and the primary literature
(DOI or arXiv ID) that grounds the effect. Unattributed folklore factors are rejected per
the quant-project rule snippet's "Published research" clause.

- **H0:**
- **H1:**
- **Mechanism:**
- **Primary citations:**

## 2. Universe and sample period

Bounded at pre-reg; no discretion later. Specify instruments, sampling frequency,
session regime, and the time-ordered train / validation / test windows. Walk-forward
only — no k-fold per the quant-project rule snippet's "Time-series integrity" clause.

- **Instruments:**
- **Frequency:**
- **Session(s):**
- **Train window:**
- **Validation window:**
- **Test window:**
- **Roll-handling note:**

## 3. Features

List feature modules by exact `FEATURE_REGISTRY` name and semver version. Any logic
change bumps `version`. Point-in-time property test and pipeline-level leakage test
must pass before run (see the `pit-canary` skill).

- **Feature entries (`name@version`):**

## 4. Label construction

Triple-barrier labeling per López de Prado AFML §3.2. Required fields (all appear in
`config.yaml` `label` block):

- **`pt_sl` (profit-take / stop-loss multipliers):**
- **`vertical_barrier` (duration):**
- **`volatility_estimator` (e.g. Yang-Zhang, Parkinson, realized-vol lookback):**
- **Meta-label horizon effective upper bound (feeds splitter `purge`):**

## 5. Estimator

Exact model class and hyperparameter grid, fixed at pre-reg. No post-hoc additions to
the grid. Hyperparameter search is nested inside walk-forward; no information leaks
from outer to inner folds.

- **Model class:**
- **Hyperparameter grid:**
- **Search protocol (grid / random / Bayesian, with budget):**
- **Loss / metric:**

## 6. Splitter

`PurgedWalkForwardSplitter` or `CombinatorialPurgedCV` per López de Prado AFML §7+§12.
`embargo` is data-driven (residual PACF vs Politis-White block length, max);
`purge >= max label horizon`. CPCV `n_groups` and `n_test_groups` are hypothesis-level
choices logged with rationale.

- **Splitter choice:**
- **`embargo` selection method:**
- **`purge` derivation:**
- **If CPCV: `n_groups`, `n_test_groups`, selection rationale:**

## 7. Cost model

Reference `cost_model_id` registered in the project's cost-model package. Slippage is
regime-conditional (RTH/ETH/OVN) and fit walk-forward, never single-split.

- **`cost_model_id`:**
- **Commission schedule source:**
- **Slippage model version:**

## 8. Gate thresholds

Gate-report fields and thresholds. Any deviation from project-level defaults must be
justified here with a `# justify:` note and a citation.

- **`alpha`:**
- **`bh_threshold` (BH-FDR threshold):**
- **`dsr_activation_size` (Deflated Sharpe Ratio activation):**
- **Power target:**

## 9. Stopping rule

Pre-specified criterion for terminating the run. No p-hacking; no "keep training until
Sharpe crosses X" (Sharpe is reporting-only, never an optimization target). Either:
(a) fixed number of walk-forward folds, or (b) calendar-time budget, or
(c) futility check against `n_required_for_power_80`.

- **Stop criterion:**
- **Max folds:**
- **Max wall-clock budget:**

## 10. Decision rule

Mapping from gate outcome to archival label and next action. Null results stay in the
hypothesis register per the non-loss policy.

- **If `passed=True`:** archive(positive), promote to paper-trade eligibility list.
- **If `passed=False` and CI excludes zero but SPA fails:** archive(null) with
  multiple-testing note.
- **If `passed=False` and CI covers zero:** archive(null).
- **If realized n < pre-registered `n_required_for_power_80`:** archive(null,
  underpowered).

## 11. Reproducibility commitments

Log the tuple required by the project reproducibility envelope per the repository
`AGENTS.md` and the ReproLog schema:

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** {{SEED}}  # justify: pre-registered; do not modify post-hoc
- **Dataset checksums (frozen at pre-reg from `data/_manifest.json`):**
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
- **Design.md SHA at freeze:** auto-populated by `pre-register-hypothesis`
