---
name: power-analysis
description: Pre-data power / sample-size analysis for a planned hypothesis. Invoked AFTER pre-registration and BEFORE validate-data. Computes required n for the registered effect of interest at the registered alpha/power target. Retrospective (post-hoc) power use is forbidden per Hoenig & Heisey 2001.
---

# power-analysis

## When to invoke

After `pre-register-hypothesis` has frozen the design.md, and BEFORE any data validation or model fit. Gate position:

```
hypothesis-new
    └─► pre-register-hypothesis
        └─► power-analysis                  ← THIS SKILL
            └─► validate-data
                └─► statistical-analysis
```

This ordering matters: power analysis informs whether n is adequate for the registered effect of interest. If projected n is insufficient, the user MUST either (a) increase the sample, (b) revise the effect of interest downward (with a new pre-registration), or (c) abandon the hypothesis. Proceeding with an underpowered design corrupts the inferential record.

## Retrospective-power prohibition

**Do not use this skill to compute "observed power" after the analysis is run.** Hoenig & Heisey 2001 [^1] showed that post-hoc power based on observed effect size is monotone in p-value — it adds no information beyond the p-value and is at best misleading, at worst circular. The only legitimate use is design-time, with a pre-specified (not observed) effect of interest.

## Procedure

1. **Read the pre-registered design.md** for the hypothesis ID. Extract:
   - Effect of interest (from §1 H1): point estimate of the smallest scientifically-meaningful effect (NOT the literature-reported effect; the latter is anchoring bias).
   - Alpha (from §8): pre-registered significance threshold.
   - Power target (from §8): typically 0.80 but project-pre-registered.
   - Test type (from §5): two-sample t / one-sample / regression coefficient / proportion / time-to-event log-rank / etc.

2. **Compute required n** via the appropriate `statsmodels.stats.power` function:
   - `tt_ind_solve_power` — two-sample t-test (Cohen-d effect size)
   - `tt_solve_power` — one-sample / paired
   - `NormalIndPower().solve_power(...)` with `effect_size = statsmodels.stats.proportion.proportion_effectsize(p1, p2)` (Cohen's h transform per Cohen 1988 §6.2) — two-proportion z-test. NOTE: `zt_ind_solve_power` is the z-test for two-sample means under known variance, NOT for proportions; a common confusion.
   - `FTestPower` — F-test / ANOVA / regression overall F
   - `NormalIndPower` — generic z-test
   - For survival: `lifelines.statistics.power_calculation` or analytical Schoenfeld formula

   Cite the function used; `# justify:` comment on the call site explains why this is the right test for the design.

3. **Grid-search over a range of effect sizes** to expose sensitivity. Grid endpoints:
   - Lower: 50% of the registered effect (under-power case)
   - Upper: 200% of the registered effect (over-power case)
   - 5-10 intermediate points

4. **Write the output artifact** to `research/01_hypothesis_register/<HID>/power_analysis_{YYYY-MM-DD}.md`. Required sections:

   ```markdown
   ---
   title: Power analysis — <HID>
   date: <YYYY-MM-DD>
   hypothesis_id: <HID>
   type: power_analysis
   ---

   # Power analysis for <HID>

   ## Pre-registered parameters
   | Param | Value | Source |
   |---|---|---|
   | Effect of interest | <value>  # justify: from design.md §1 H1, smallest scientifically-meaningful effect | design.md SHA <sha> |
   | Alpha | <value>  # justify: from design.md §8 | design.md §8 |
   | Power target | <value>  # justify: from design.md §8 | design.md §8 |
   | Test type | <name> | design.md §5 |

   ## Required n (point estimate)

   At the registered effect, alpha, and power target: **n = <value>** per group (or total).

   ## Sensitivity grid

   | Effect size | Required n | Notes |
   |---|---|---|
   ...

   ## Disposition

   - **If realized sample size >= required n at the registered effect:** proceed to validate-data.
   - **If realized sample size < required n at the registered effect:** ARCHIVE the hypothesis as underpowered (per design.md §10), OR revise the pre-registration (new HID).

   ## References
   - Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed. ISBN 978-0805802832.
   - Champely, S. *pwr* R package. https://cran.r-project.org/web/packages/pwr/
   - Hoenig, J. M., & Heisey, D. M. (2001). "The Abuse of Power." *Am Stat* 55:19. https://doi.org/10.1198/000313001300339897 — retrospective power is uninformative and should not be reported.

   ## Reproducibility
   ReproLog: `logs/reproducibility/repro_log_<run_id>.json` (phase=validation; hypothesis_id=<HID>).
   ```

5. **Emit ReproLog** at `logs/reproducibility/repro_log_<run_id>.json` with:
   - `phase = "validation"`
   - `hypothesis_id = H<NNN>`
   - `rng_seed = <pre-registered seed from design.md §11>`
   - `config_resolved_sha256 = <SHA of the power_analysis_{date}.md file>`

6. **Commit via `commit-with-provenance`** with `--role=audit` (power analysis is design-time audit of the pre-reg's adequacy).

## Magic-numbers enforcement

This skill body INSTRUCTS the user to add `# justify:` neighbors on every numeric arg of the power call. Verification is by `quant-auditor` agent at audit-loop time, not by a pre-write hook.

## Hand-off

- Reads from `pre-register-hypothesis` output: `research/01_hypothesis_register/<HID>/design.md`.
- Writes to: `research/01_hypothesis_register/<HID>/power_analysis_{date}.md`.
- Emits ReproLog via [emit-repro-log](../emit-repro-log/SKILL.md).
- Hands off to existing [validate-data](../validate-data/SKILL.md) next.
- Audit at `audit-remediate-loop` via `quant-auditor`.

## References

[^1]: Hoenig, J. M., & Heisey, D. M. (2001). "The Abuse of Power: The Pervasive Fallacy of Power Calculations for Data Analysis." *Am Stat* 55(1):19-24. https://doi.org/10.1198/000313001300339897
[^2]: Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed. Lawrence Erlbaum. ISBN 978-0805802832.
[^3]: Champely, S. *pwr*. CRAN. https://cran.r-project.org/web/packages/pwr/
[^4]: statsmodels.stats.power documentation. https://www.statsmodels.org/stable/api.html#statsmodels.stats.power
[^5]: Davidson-Pilon, C. (2019). lifelines. *JOSS* 4(40):1317. https://doi.org/10.21105/joss.01317 — survival-analysis power via Schoenfeld formula.
