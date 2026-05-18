---
title: <<TITLE>>
author: <<AUTHOR>>
date: <<DATE>>
reporting_standard: TRIPOD+AI 2024
study_design: <<prediction model development | validation | combined>>
preregistration_sha256: <<sha256>>
ai_assistance: <<MODEL_ID>> (role=<<role>>; per ICMJE 2026)
---

<!-- TRIPOD+AI 2024 — Collins et al. BMJ 385:e078378 — https://doi.org/10.1136/bmj-2023-078378 -->
<!-- 27-item updated checklist for prediction models including ML/AI models. -->

# <<TITLE>>

<!-- TRIPOD+AI 1: Identify as developing/validating a prediction model in title -->
<!-- TRIPOD+AI 2: Structured abstract -->

## Abstract

**Objectives:** <!-- TODO -->

**Methods:** <!-- TODO; data source, predictors, outcome, model type -->

**Results:** <!-- TODO; discrimination + calibration -->

**Conclusions:** <!-- TODO -->

## Introduction

<!-- TRIPOD+AI 3a: Background — burden, current diagnostic/prognostic approaches, gap -->
<!-- TRIPOD+AI 3b: Specific objectives -->

## Methods

<!-- TRIPOD+AI 4a: Source of data (registry, RCT, cohort, EHR, claims) -->
<!-- TRIPOD+AI 4b: Dates of participant enrolment, follow-up, location -->
### Data source

<!-- TRIPOD+AI 5a: Eligibility criteria — inclusion/exclusion -->
<!-- TRIPOD+AI 5b: Treatments received and whether at random -->
### Participants

<!-- TRIPOD+AI 6a: Outcome definition, measurement, scoring/labelling, blinding -->
<!-- TRIPOD+AI 6b: For binary: cut-off value rationale -->
### Outcome

<!-- TRIPOD+AI 7a: Predictors used to develop model; how/when measured -->
<!-- TRIPOD+AI 7b: For ML models: feature engineering, normalisation, transformations -->
### Predictors

<!-- TRIPOD+AI 8: Sample size — number of events, n per predictor (≥10 for logistic; ≥20 for some ML), training/validation/test split -->
### Sample size

Pre-data power analysis per [skills/power-analysis](../../skills/power-analysis/SKILL.md); for prediction models the "effect of interest" is target AUC at registered confidence.

<!-- TRIPOD+AI 9: Missing data — handling (multiple imputation per White, Royston, Wood 2011 if MAR) -->
### Missing data

<!-- TRIPOD+AI 10a: Statistical analysis methods — model derivation -->
<!-- TRIPOD+AI 10b: Calibration assessment -->
<!-- TRIPOD+AI 10c: Discrimination assessment (AUC, c-statistic) -->
<!-- TRIPOD+AI 10d: Validation method (internal: bootstrap, k-fold; external: temporal, geographic) -->
### Statistical methods

For time-series data: walk-forward CV per the quant-cwd rule snippet; never k-fold. Purge + embargo per López de Prado 2018 §7.

<!-- TRIPOD+AI 11: Risk groups (if applicable) — how defined -->
### Risk groups

<!-- TRIPOD+AI 12: Development vs validation — clearly distinguished -->
### Development vs validation

## Results

<!-- TRIPOD+AI 13a: Flow of participants (development + validation) -->
<!-- TRIPOD+AI 13b: Demographics and clinical characteristics of participants -->
### Participants

<!-- TRIPOD+AI 14: Model development — final number of predictors retained, shrinkage if used -->
### Model specification

<!-- TRIPOD+AI 15: Model performance — discrimination AUC + 95% CI; calibration slope + intercept; Brier score -->
### Performance

| Metric | Development | Internal validation | External validation |
|---|---|---|---|
| AUC (95% CI) | | | |
| Calibration slope | | | |
| Calibration intercept | | | |
| Brier score | | | |

<!-- TRIPOD+AI 16: Model updating (if applicable) -->
### Model updating

<!-- TRIPOD+AI 17: Subgroup performance, fairness metrics for AI models -->
### Subgroup / fairness

For AI/ML models, report performance disaggregated by relevant subgroups (age, sex, race/ethnicity, socioeconomic strata) and assess fairness metrics (equal opportunity, demographic parity, calibration within groups).

## Discussion

<!-- TRIPOD+AI 18: Limitations — overfitting, data quality, generalisability -->
### Limitations

<!-- TRIPOD+AI 19: Interpretation — clinical utility, decision-curve analysis -->
### Interpretation

<!-- TRIPOD+AI 20: Implications for practice + research -->
### Implications

## Other information

<!-- TRIPOD+AI 21: Registration -->
### Pre-registration
- `docs/protocol/protocol_v0.md` (SHA-256: <<PREREG_SHA>>)

<!-- TRIPOD+AI 22: Protocol availability -->
<!-- TRIPOD+AI 23: Funding -->
### Funding

<!-- TRIPOD+AI 24: Data and code availability — encouraged for reproducibility -->
### Data and code availability
- Data: `data/_manifest.json` (per the data-manifest schema)
- Code: https://github.com/<<GITHUB_HANDLE>>/<<REPO>>; commit <<BOOTSTRAP_SCRIPT_HEAD>>
- ReproLog: `logs/reproducibility/repro_log_<run_id>.json` (13 fields per the emit-repro-log schema)
- Model artifacts: `artifacts/models/` (SHA-256 in ReproLog `model_hash`)

<!-- TRIPOD+AI 25: AI-specific: model card, intended use, contraindications -->
### Model card
See `docs/model_card_<<NAME>>.md` (Mitchell et al. 2019 FAT* — https://doi.org/10.1145/3287560.3287596).

<!-- TRIPOD+AI 26: AI-specific: dataset card (Gebru et al. 2021 Datasheets for Datasets) -->
### Dataset card
See `docs/dataset_card_<<DATASET>>.md` (Gebru et al. 2021 *Commun ACM* 64(12):86 — https://doi.org/10.1145/3458723).

<!-- TRIPOD+AI 27: AI-specific: human oversight + monitoring plan -->
### Monitoring and oversight

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../docs/ai_assistance_statement.md) (ICMJE 2026).

## References

<!-- Vancouver; auto-populated via /cite-add. -->
