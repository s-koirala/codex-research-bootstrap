---
title: <<TITLE>>
author: <<AUTHOR>>
date: <<DATE>>
reporting_standard: STROBE
study_design: <<cohort | case-control | cross-sectional>>
preregistration_sha256: <<sha256 of docs/protocol/protocol_v0.md>>
ai_assistance: <<MODEL_ID>> (role=<<idea|code|prose|audit|multi>>; per ICMJE 2026)
---

<!-- STROBE 2007 — von Elm et al. PLOS Med 4(10):e296 — https://doi.org/10.1371/journal.pmed.0040296 -->
<!-- Reporting standard: STROBE 22-item checklist for observational studies (cohort / case-control / cross-sectional). -->
<!-- Item-level guidance: https://www.strobe-statement.org/checklists/ -->

# <<TITLE>>

<!-- STROBE item 1(a): Indicate the study's design with a commonly used term in the title or the abstract -->
<!-- STROBE item 1(b): Provide in the abstract an informative and balanced summary -->

## Abstract

**Background:** <!-- TODO -->

**Methods:** <!-- TODO -->

**Results:** <!-- TODO -->

**Conclusions:** <!-- TODO -->

## Introduction

<!-- STROBE item 2: Background/rationale -->
### Background

<!-- STROBE item 3: Objectives — specify pre-specified hypotheses; cite design.md SHA -->
### Objectives

## Methods

<!-- STROBE item 4: Study design — key elements early in the paper -->
### Study design

<!-- STROBE item 5: Setting — locations, relevant dates, periods, exposures, follow-up, data collection -->
### Setting

<!-- STROBE item 6: Participants — eligibility, sources, methods of selection -->
### Participants

<!-- STROBE item 7: Variables — outcomes, exposures, predictors, confounders, effect modifiers; diagnostic criteria -->
### Variables

<!-- STROBE item 8: Data sources and measurement — for each variable of interest -->
### Data sources and measurement

<!-- STROBE item 9: Bias — describe efforts to address potential sources -->
### Addressing bias

<!-- STROBE item 10: Study size — explain how arrived at -->
### Sample size

<!-- STROBE item 11: Quantitative variables — handling in analyses -->
### Quantitative variables

<!-- STROBE item 12(a-e): Statistical methods — control of confounding, subgroups, missing data, sensitivity, loss to follow-up -->
### Statistical methods

E-value sensitivity (VanderWeele & Ding 2017 *Ann Intern Med* 167(4):268; https://doi.org/10.7326/M16-2607) is computed for every primary causal estimate per the epi-cwd rule snippet. DAG-derived back-door adjustment set per Pearl 2009 §3.3.

## Results

<!-- STROBE item 13(a-c): Participants — numbers at each stage, reasons for non-participation, flow diagram -->
### Participants

<!-- STROBE item 14(a-c): Descriptive data — characteristics, missing data, follow-up time -->
### Descriptive data

<!-- STROBE item 15: Outcome data — numbers of outcome events / summary measures over time -->
### Outcome data

<!-- STROBE item 16(a-c): Main results — unadjusted/adjusted estimates with CIs; category boundaries; relative risk → absolute risk for meaningful period -->
### Main results

| Outcome | n | Unadjusted | Adjusted | 95% CI | E-value |
|---|---|---|---|---|---|
| <!-- primary --> | | | | | |

<!-- STROBE item 17: Other analyses — subgroups, interactions, sensitivity -->
### Subgroup and sensitivity analyses

## Discussion

<!-- STROBE item 18: Key results — summary with reference to objectives -->
### Key results

<!-- STROBE item 19: Limitations — sources of bias, imprecision -->
### Limitations

<!-- STROBE item 20: Interpretation — cautious, considering objectives, limitations, multiplicity, evidence -->
### Interpretation

<!-- STROBE item 21: Generalisability — external validity -->
### Generalisability

## Other information

<!-- STROBE item 22: Funding — source of funding; role in present and original study -->
### Funding

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../docs/ai_assistance_statement.md) (ICMJE 2026; https://www.icmje.org/recommendations/).

### Pre-registration
- Protocol: `docs/protocol/protocol_v0.md` (SHA-256: <<PREREG_SHA>>)
- External registry: <<OSF DOI if any; otherwise omit>>

### Data and code availability
- Data: `data/_manifest.json` (per-file SHA-256 + provenance per the data-manifest schema)
- Code: https://github.com/<<GITHUB_HANDLE>>/<<REPO>>; commit <<BOOTSTRAP_SCRIPT_HEAD>>
- ReproLog: `logs/reproducibility/repro_log_<run_id>.json` (13 fields per the emit-repro-log schema)

## References

<!-- Vancouver style; numbered. References auto-populated via /cite-add (CrossRef MCP). -->
<!-- See CITATION.cff for the machine-readable reference list. -->
