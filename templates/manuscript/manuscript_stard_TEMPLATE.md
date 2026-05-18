---
title: <<TITLE>>
author: <<AUTHOR>>
date: <<DATE>>
reporting_standard: STARD 2015
study_design: diagnostic accuracy
preregistration_sha256: <<sha256>>
ai_assistance: <<MODEL_ID>> (role=<<role>>; per ICMJE 2026)
---

<!-- STARD 2015 — Bossuyt et al. BMJ 351:h5527 — https://doi.org/10.1136/bmj.h5527 -->
<!-- 30-item checklist for studies of diagnostic test accuracy. -->
<!-- Portal: https://www.equator-network.org/reporting-guidelines/stard/ -->

# <<TITLE>>

<!-- STARD 1: Identification as diagnostic accuracy study using at least one measure of accuracy (sensitivity, specificity, etc.) in title or abstract -->
<!-- STARD 2: Structured abstract -->

## Abstract

**Background:** <!-- TODO -->

**Methods:** <!-- TODO; index test, reference standard, target condition -->

**Results:** <!-- TODO; sensitivity/specificity/PPV/NPV with 95% CIs -->

**Conclusions:** <!-- TODO -->

## Introduction

<!-- STARD 3: Scientific and clinical background -->
<!-- STARD 4: Study objectives and hypotheses -->

## Methods

<!-- STARD 5: Cohort or case-control design -->
### Study design

<!-- STARD 6: Eligibility criteria -->
<!-- STARD 7: Identification and recruitment -->
### Participants

<!-- STARD 8: Description of the index test (how performed, interpreted) -->
### Index test(s)

<!-- STARD 9: Description of reference standard (how performed, interpreted) -->
### Reference standard

<!-- STARD 10a: Categories of test results -->
<!-- STARD 10b: Threshold/cut-off values, if any, with rationale -->
### Test results categorization

<!-- STARD 11: Whether clinical information and reference standard results were available to performers/readers of index test -->
<!-- STARD 12: Whether clinical information and index test results were available to assessors of reference standard -->
### Blinding

<!-- STARD 13a: Methods for estimating diagnostic accuracy or comparing accuracy -->
<!-- STARD 13b: Methods for quantifying variability (CIs) -->
<!-- STARD 14: Sample size — how determined -->
<!-- STARD 15: Indeterminate results: how handled -->
<!-- STARD 16: Missing data on index test/reference standard: how handled -->
### Analysis

## Results

<!-- STARD 17: Participant flow diagram — exclusions at each stage -->
### Participant flow

<!-- STARD 18: Baseline demographic and clinical features of included participants -->
### Baseline characteristics

<!-- STARD 19: Distribution of severity of disease (those with target condition); other diagnoses (those without) -->
### Distribution of disease severity

<!-- STARD 20: Time interval between index test and reference standard -->
### Test sequencing

<!-- STARD 21a: Cross-tabulation: index test by reference standard (2x2 if binary) -->
<!-- STARD 21b: Test accuracy estimates with 95% CIs -->
### Test accuracy

| Index test | Reference + | Reference − | Total |
|---|---|---|---|
| Positive | TP | FP | |
| Negative | FN | TN | |
| Total | | | |

| Metric | Estimate | 95% CI |
|---|---|---|
| Sensitivity | | |
| Specificity | | |
| PPV | | |
| NPV | | |
| LR+ | | |
| LR− | | |

<!-- STARD 22: How indeterminate results, missing data, outliers were handled -->
<!-- STARD 23: Variability of accuracy across subgroups -->
### Subgroup analyses

<!-- STARD 24: Adverse events from index test or reference standard -->
### Adverse events

## Discussion

<!-- STARD 25: Limitations — internal validity, external validity, statistical uncertainty -->
### Limitations

<!-- STARD 26: Implications for practice — actionable recommendations -->
### Clinical implications

<!-- STARD 27: Other studies — comparison with prior work -->
### Comparison with prior work

## Other information

<!-- STARD 28: Registration number -->
<!-- STARD 29: Where study protocol can be accessed -->
### Pre-registration
- `docs/protocol/protocol_v0.md` (SHA-256: <<PREREG_SHA>>)

<!-- STARD 30: Sources of funding -->
### Funding

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../docs/ai_assistance_statement.md) (ICMJE 2026).

### Data and code availability
- Data: `data/_manifest.json` (per the data-manifest schema)
- Code: https://github.com/<<GITHUB_HANDLE>>/<<REPO>>; commit <<BOOTSTRAP_SCRIPT_HEAD>>
- ReproLog: `logs/reproducibility/repro_log_<run_id>.json`

## References

<!-- Vancouver; auto-populated via /cite-add. -->
