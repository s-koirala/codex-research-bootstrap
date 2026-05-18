---
title: <<NAME>> - analysis report
date: <<YYYY-MM-DD>>
type: epi_report
reporting_standard: <<STROBE | CONSORT | STARD | TRIPOD | PRISMA>>
study_design: <<cohort | case-control | RCT | diagnostic accuracy | prediction model | systematic review>>
git_head_at_authoring: <<short_sha>>
pip_freeze_sha256: <<sha256>>
dataset_checksums_source: data/_manifest.json
rng_seed: <<int>>
ai_assistance: <<model+version>> (role=<<idea|code|prose|audit|multi>>; per ICMJE 2026)
preregistration_sha256: <<sha256 of docs/protocol/protocol_v0.md>>
---

# <<NAME>> - analysis report

> **Reporting standard claimed:** `<<STROBE | CONSORT | STARD | TRIPOD | PRISMA>>`
>
> Checklist items satisfied below carry their canonical numbering. Item gaps
> are flagged `<<TODO>>` and must be filled before submission.

## 1. Title and abstract

<<TODO: per checklist item 1>>

## 2. Introduction

### Background and rationale (item 2)
<<TODO>>

### Objectives (item 3)
<<TODO; specify estimand, target population, comparison>>

## 3. Methods

### Study design (item 4)
<<from protocol_v0.md>>

### Setting (item 5)
<<dates; locations; follow-up>>

### Participants (item 6)
<<eligibility; sources>>

### Variables (item 7)

| Variable | Type | Operational definition | Source |
|---|---|---|---|
| Outcome | <<binary | continuous | time-to-event>> | <<def>> | <<source>> |
| Exposure | <<categorical | continuous>> | <<def>> | <<source>> |
| Confounders | (set via DAG back-door) | <<list>> | <<source>> |
| Effect modifiers | (pre-specified) | <<list>> | <<source>> |

### Data sources / measurement (item 8)
<<instruments; QC; data/_manifest.json entries listed in appendix>>

### Bias (item 9)
<<selection / measurement / confounding>>

### Study size (item 10)
<<n + power-analysis result; minimum-detectable effect>>

### Quantitative variables handling (item 11)
<<categorization rationale; no magic cutoffs>>

### Statistical methods (item 12)
- Primary analysis: <<model; HAC SE if time-series; cluster-robust if grouped>>
- Subgroup analyses: <<pre-specified>>
- Sensitivity: **E-value** (VanderWeele & Ding 2017 *Ann Intern Med* 167:268; https://doi.org/10.7326/M16-2607) for every primary causal estimate.
- Multiple testing: <<BH FDR / Hansen SPA; cite>>
- Missing data: <<MCAR/MAR/MNAR + treatment>>

## 4. Results

### Participants flow (item 13)
<<n at each stage; flow-diagram path>>

### Descriptive data (item 14)
Table 1 (via `tableone`; Pollard et al. 2018 *JAMIA Open* 1(1):26):

<<TODO: insert table>>

### Outcome data (item 15)
<<events / outcomes by group>>

### Main results (item 16)

| Outcome | Estimate | 95% CI | p-value | Adjustment set |
|---|---|---|---|---|
| <<primary>> | <<value>> | <<lo, hi>> | <<value>> | <<DAG back-door set>> |

### Subgroup + sensitivity (item 17)

| Analysis | Result | E-value (for unmeasured confounding) |
|---|---|---|
| <<primary>> | <<estimate>> | <<E-value>> |
| <<subgroup A>> | <<estimate>> | <<E-value>> |

### Predictor performance (TRIPOD items 14-16; if applicable)
- Discrimination: AUC = <<value>>, 95% CI = <<lo, hi>>
- Calibration slope: <<value>>; intercept: <<value>>
- Calibration plot: <<see figures>>

## 5. Discussion

### Principal findings (item 18)
<<TODO>>

### Limitations (item 19)
<<TODO>>

### Interpretation (item 20)
<<comparison with prior work>>

### Generalizability (item 21)
<<TODO>>

## 6. Other information

### Funding (item 22)
<<TODO>>

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../../docs/ai_assistance_statement.md). ICMJE 2026 mandates model + role disclosure; AI tools cannot be authors.

### Pre-registration
- Protocol path: `docs/protocol/protocol_v0.md`
- Frozen SHA-256: <<sha>>
- External registry DOI (if any): <<OSF DOI>>

## 7. DAG

```
<<dagitty syntax via dag-drafter subagent or manual>>
```

Adjustment set (back-door criterion): <<list>>

## 8. Reproducibility appendix

- Git HEAD: <<sha>>
- `uv pip freeze` SHA-256: <<sha>>
- Dataset manifest: `data/_manifest.json`
- RNG seed: <<int>>
- ReproLog: `logs/reproducibility/repro_log_<<run_id>>.json`
- Code archive: <<TODO: project DOI>>

## 9. Referenced datasets

| Path | SHA-256 | Source URI | License | Snapshot date |
|---|---|---|---|---|
<<TODO: from data/_manifest.json>>

## 10. References

See [CITATION.cff](../../CITATION.cff) `references:`. Add via `cite-add <DOI>`.
