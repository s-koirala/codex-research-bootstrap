---
title: <<TITLE>>
author: <<AUTHOR>>
date: <<DATE>>
reporting_standard: CONSORT 2010
study_design: randomized controlled trial
trial_registration: <<ClinicalTrials.gov NCT number or other registry ID>>
preregistration_sha256: <<sha256>>
ai_assistance: <<MODEL_ID>> (role=<<role>>; per ICMJE 2026)
---

<!-- CONSORT 2010 — Schulz, Altman, Moher BMJ 340:c332 — https://doi.org/10.1136/bmj.c332 -->
<!-- 25-item checklist for parallel-group randomized trials. -->
<!-- Portal: https://www.consort-statement.org/ -->

# <<TITLE>>

<!-- CONSORT 1a: Identification as a randomised trial in the title -->
<!-- CONSORT 1b: Structured abstract — design, methods, results, conclusions -->

## Abstract

**Trial registration:** <<NCT number>>

**Background:** <!-- TODO -->

**Methods:** <!-- TODO; declare randomization unit, allocation ratio -->

**Results:** <!-- TODO; per-group n, primary outcome with CI -->

**Conclusions:** <!-- TODO -->

## Introduction

<!-- CONSORT 2a: Scientific background and rationale -->
### Background

<!-- CONSORT 2b: Specific objectives or hypotheses -->
### Objectives

## Methods

<!-- CONSORT 3a: Trial design (parallel, factorial, crossover, cluster) with allocation ratio -->
<!-- CONSORT 3b: Important changes to methods after trial commencement (with reasons) -->
### Trial design

<!-- CONSORT 4a: Eligibility criteria for participants -->
<!-- CONSORT 4b: Settings and locations where data collected -->
### Participants

<!-- CONSORT 5: Interventions for each group with sufficient detail for replication -->
### Interventions

<!-- CONSORT 6a: Completely defined pre-specified primary and secondary outcomes -->
<!-- CONSORT 6b: Any changes to outcomes after trial commencement (with reasons) -->
### Outcomes

<!-- CONSORT 7a: How sample size determined -->
<!-- CONSORT 7b: Interim analyses and stopping guidelines -->
### Sample size

Pre-data power analysis per [skills/power-analysis](../../skills/power-analysis/SKILL.md); retrospective power use is forbidden per Hoenig & Heisey 2001 [*Am Stat* 55(1):19](https://doi.org/10.1198/000313001300339897).

<!-- CONSORT 8a: Method used to generate random allocation sequence -->
<!-- CONSORT 8b: Type of randomisation; details of any restriction (eg, blocking, block size) -->
<!-- CONSORT 9: Mechanism used to implement random allocation sequence -->
<!-- CONSORT 10: Who generated, who enrolled, who assigned -->
### Randomisation

<!-- CONSORT 11a: Blinding of participants, providers, outcome assessors -->
<!-- CONSORT 11b: Similarity of interventions if blinding -->
### Blinding

<!-- CONSORT 12a: Statistical methods for primary and secondary outcomes -->
<!-- CONSORT 12b: Subgroup and adjusted analyses methods -->
### Statistical methods

## Results

<!-- CONSORT 13a: Flow diagram — numbers of participants randomly assigned, received treatment, analyzed for primary outcome -->
<!-- CONSORT 13b: Losses and exclusions after randomisation, with reasons -->
### Participant flow

**Figure 1.** CONSORT flow diagram. <!-- generate via dag-drafter or PRISMA-style flow tool -->

<!-- CONSORT 14a: Dates of recruitment and follow-up -->
<!-- CONSORT 14b: Why trial ended or stopped (if applicable) -->
### Recruitment

<!-- CONSORT 15: Table of baseline demographic and clinical characteristics by group -->
### Baseline characteristics

| Variable | Group A (n=) | Group B (n=) |
|---|---|---|

<!-- CONSORT 16: Numbers analyzed in each group, intention-to-treat -->
### Numbers analyzed

<!-- CONSORT 17a: Primary and secondary outcomes — results for each group, estimated effect size and precision (95% CI) -->
<!-- CONSORT 17b: Binary outcomes — absolute and relative effect sizes -->
### Outcomes and estimation

| Outcome | Group A | Group B | Effect (95% CI) | p-value |
|---|---|---|---|---|

<!-- CONSORT 18: Subgroup analyses — pre-specified vs exploratory -->
### Subgroup analyses

<!-- CONSORT 19: Important harms or unintended effects in each group -->
### Harms

## Discussion

<!-- CONSORT 20: Trial limitations — sources of potential bias, imprecision, multiplicity -->
### Limitations

<!-- CONSORT 21: Generalisability (external validity) of trial findings -->
### Generalisability

<!-- CONSORT 22: Interpretation consistent with results, balancing benefits and harms -->
### Interpretation

## Other information

<!-- CONSORT 23: Registration number and trial register -->
### Registration

<!-- CONSORT 24: Where protocol can be accessed -->
### Protocol
- `docs/protocol/protocol_v0.md` (SHA-256: <<PREREG_SHA>>)

<!-- CONSORT 25: Sources of funding and role -->
### Funding

### AI-assistance disclosure
See [docs/ai_assistance_statement.md](../docs/ai_assistance_statement.md) (ICMJE 2026).

### Data and code availability
- Data: `data/_manifest.json` (per-file SHA-256 + provenance per the data-manifest schema)
- Code: https://github.com/<<GITHUB_HANDLE>>/<<REPO>>; commit <<BOOTSTRAP_SCRIPT_HEAD>>
- ReproLog: `logs/reproducibility/repro_log_<run_id>.json`

## References

<!-- Vancouver; auto-populated via /cite-add. -->
