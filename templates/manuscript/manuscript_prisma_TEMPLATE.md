---
title: <<TITLE>>
author: <<AUTHOR>>
date: <<DATE>>
reporting_standard: PRISMA 2020
study_design: systematic review
review_registration: <<PROSPERO CRD number>>
preregistration_sha256: <<sha256 of docs/protocol/protocol_v0.md>>
ai_assistance: <<MODEL_ID>> (role=<<role>>; per ICMJE 2026)
---

<!-- PRISMA 2020 — Page et al. BMJ 372:n71 — https://doi.org/10.1136/bmj.n71 -->
<!-- 27-item checklist + flow diagram for systematic reviews. -->
<!-- Portal: https://prisma-statement.org/ -->
<!-- Flow diagram generator: https://prisma.shinyapps.io/prisma2020/ -->

# <<TITLE>>

<!-- PRISMA 1: Identify as systematic review in title -->
<!-- PRISMA 2: Structured abstract — see PRISMA 2020 for Abstracts checklist -->

## Abstract

**Background:** <!-- TODO -->

**Objectives:** <!-- TODO -->

**Methods:** <!-- TODO; databases searched, study selection, synthesis -->

**Results:** <!-- TODO; n studies, main findings, certainty -->

**Conclusions:** <!-- TODO -->

**Registration:** <<PROSPERO CRD number>>

## Introduction

<!-- PRISMA 3: Rationale -->
### Rationale

<!-- PRISMA 4: Objectives — research question framed using PICO(S) or similar -->
### Objectives

PICO(S):
- **Population:** <!-- -->
- **Intervention / exposure:** <!-- -->
- **Comparator:** <!-- -->
- **Outcome:** <!-- -->
- **Study designs:** <!-- -->

## Methods

<!-- PRISMA 5: Eligibility criteria — characteristics used, how grouped -->
### Eligibility criteria

<!-- PRISMA 6: Information sources — databases, registers, websites, dates of last search -->
### Information sources

<!-- PRISMA 7: Search strategy — full strategies for ALL databases (typically appendix) -->
### Search strategy

Full search strategies in supplementary appendix `manuscript/supplement/search_strategies.md`.

<!-- PRISMA 8: Selection process — how decisions made at each stage, n reviewers, automation tools -->
### Selection process

<!-- PRISMA 9: Data collection process — methods, n reviewers, automation -->
### Data extraction

<!-- PRISMA 10a: List and define all variables for which data sought -->
<!-- PRISMA 10b: Assumption + simplification methods -->
### Data items

<!-- PRISMA 11: Risk of bias assessment — tool used, who, n reviewers -->
### Risk of bias

<!-- PRISMA 12: Effect measures (RR, OR, HR, MD, SMD) -->
### Effect measures

<!-- PRISMA 13a: Tabulation/visual display methods -->
<!-- PRISMA 13b: Statistical synthesis methods (meta-analysis if applicable; heterogeneity statistics) -->
<!-- PRISMA 13c-f: Subgroup analyses, sensitivity, certainty methods -->
### Synthesis methods

<!-- PRISMA 14: Reporting bias assessment (publication bias) -->
### Reporting bias assessment

<!-- PRISMA 15: Certainty assessment — GRADE typically -->
### Certainty assessment (GRADE)

## Results

<!-- PRISMA 16a: Study selection — results of search and selection; PRISMA flow diagram -->
<!-- PRISMA 16b: Citations of studies that might appear to meet inclusion but were excluded -->
### Study selection

**Figure 1.** PRISMA 2020 flow diagram (rendered via https://prisma.shinyapps.io/prisma2020/).

<!-- PRISMA 17: Study characteristics — citation of each study; reference details -->
### Study characteristics

<!-- PRISMA 18: Risk of bias of individual studies -->
### Risk of bias in studies

<!-- PRISMA 19: Results of individual studies — summary statistics + effect estimates + CIs (forest plot if meta-analysis) -->
### Results of individual studies

<!-- PRISMA 20a-d: Results of syntheses — pooled estimate, heterogeneity, subgroups, sensitivity -->
### Results of syntheses

<!-- PRISMA 21: Reporting bias — funnel plot, Egger test, etc. -->
### Reporting bias

<!-- PRISMA 22: Certainty of evidence — GRADE table -->
### Certainty of evidence

## Discussion

<!-- PRISMA 23a: General interpretation of results -->
<!-- PRISMA 23b: Limitations of evidence -->
<!-- PRISMA 23c: Limitations of review process -->
<!-- PRISMA 23d: Implications for practice, policy, future research -->

### Interpretation

### Limitations of evidence

### Limitations of review process

### Implications

## Other information

<!-- PRISMA 24a-c: Registration and protocol availability -->
### Registration and protocol
- PROSPERO registration: <<PROSPERO_CRD>>
- Protocol: `docs/protocol/protocol_v0.md` (SHA-256: <<PREREG_SHA>>)
- Amendments: documented in CHANGELOG.md

<!-- PRISMA 25: Support — sources of financial / non-financial support -->
### Support

<!-- PRISMA 26: Competing interests -->
### Competing interests

<!-- PRISMA 27: Availability of data, code, other materials -->
### Data and code availability
- Search strategies: `manuscript/supplement/search_strategies.md`
- Extracted data: `data/processed/extraction_<<DATE>>.csv` (SHA in `data/_manifest.json`)
- Analysis code: https://github.com/<<GITHUB_HANDLE>>/<<REPO>>; commit <<BOOTSTRAP_SCRIPT_HEAD>>
- ReproLog: `logs/reproducibility/repro_log_<run_id>.json`

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../docs/ai_assistance_statement.md) (ICMJE 2026).

## References

<!-- Vancouver; auto-populated via /cite-add. -->
