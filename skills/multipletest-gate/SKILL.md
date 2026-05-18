---
name: multipletest-gate
description: Family-wise multiple-testing register and gate. Maintains `config/multipletest_family.yaml` per project; blocks an inference run that adds to the family without proper correction. Applies Hansen SPA / White Reality Check / Benjamini-Hochberg FDR / Holm depending on the registered correction method.
---

# multipletest-gate

## When to invoke

Whenever a new test is being added to the project's strategy family (quant) or hypothesis family (epi). Run BEFORE recording the p-value as final; the gate computes the corrected threshold and either accepts or rejects.

Cwd-scoped to projects that have `config/multipletest_family.yaml` (created from template at first use).

## Why family-wise gating

Per the quant-project rule snippet: "Multiple testing across strategies: White 2000 reality check or Hansen 2005 SPA." Per the population-health rule snippet: "Multiple comparisons → Benjamini-Hochberg FDR unless family-wise control is required (then Holm)."

Project-level multiple-testing family must be tracked explicitly. The family register is the auditable ledger of every test ever added; without it, family scope drifts and corrected thresholds become meaningless.

## Procedure

1. **Locate `config/multipletest_family.yaml`** at project root. If absent, copy from `multipletest_family_TEMPLATE.yaml` (ships under `templates/` in this bootstrap) and prompt the user for `family_id` + `correction_method`.

2. **Read the family register.** Schema:
   ```yaml
   family_id: <unique_id>
   created: <YYYY-MM-DD>
   correction_method: <hansen_spa | white_rc | bh_fdr | holm>
   alpha_FWE: <value>  # justify: pre-registered FWE alpha; do not modify post-hoc
   hypotheses:
     - hid: H001
       raw_p: <value>
       sample_size: <n>
       registered_at: <ISO date>
     - ...
   ```

3. **Compute corrected threshold** depending on method:
   - **Hansen SPA**: bootstrap resample `n_boot = 1000`  # justify: Davison & Hinkley 1997 §2.5.1 + Efron & Tibshirani 1993 §19 — generic bootstrap-replicate convention for Monte-Carlo precision. Hansen 2005 uses bootstrap replicates in its Monte Carlo studies but does not prescribe a specific B; the 1000 value is community-canonical. Override per project if higher precision needed.
   - **White Reality Check**: similar bootstrap (Politis-Romano stationary). Test for any strategy outperforming the benchmark.
   - **Benjamini-Hochberg FDR**: rank raw p-values; threshold[k] = (k/m) × alpha. Statsmodels `multipletests(method='fdr_bh')`.
   - **Holm**: rank raw p-values; threshold[k] = alpha / (m - k + 1). Conservative FWE control.

4. **Compare**: if `raw_p < corrected_threshold`, the new test passes the family-wise gate. Otherwise, fail.

5. **Update the register** by appending the new hypothesis row. If the test failed the gate, mark `status: archive(null, family_wise_rejected)` and skip the appendix.

6. **Emit ReproLog** with `phase=validation`, `hypothesis_id=<HID>`, `rng_seed=<bootstrap seed>`.

7. **Commit via `commit-with-provenance`** with `--role=audit`.

## Fixture: Hansen 2005 Table 1 replay

For verification: replay Hansen 2005 *J Bus Econ Stat* 23(4) Table 1 (10 forecasters, IID resample, n=1000). Adjusted thresholds should match published values to 3 decimal places. Without this fixture available, fail-safe: the skill outputs the correction method, the corrected threshold, and the raw inputs — the user can verify against the canonical published values manually.

## Limitations

- The "family" must be pre-registered. If hypotheses are added after-the-fact, family-wise correction is invalidated. The register's `registered_at` field is the audit anchor.
- For strategy-universe MULTIPLE-TESTING across heterogeneous hypothesis families (e.g., one quant + one epi in the same repo), prefer separate registers per family.

## Hand-off

- Reads from project: `config/multipletest_family.yaml`.
- Emits ReproLog via [emit-repro-log](../emit-repro-log/SKILL.md).
- Hand-off to [`quant-auditor`](../../.codex/agents/quant-auditor.toml) for verification of corrected p-values.

## References

- Hansen, P. R. (2005). "A Test for Superior Predictive Ability." *J Bus Econ Stat* 23(4):365. https://doi.org/10.1198/073500105000000063 — SPA test.
- White, H. (2000). "A Reality Check for Data Snooping." *Econometrica* 68(5):1097. https://doi.org/10.1111/1468-0262.00152 — White reality check.
- Benjamini, Y., & Hochberg, Y. (1995). "Controlling the false discovery rate." *J R Stat Soc B* 57(1):289. — BH-FDR.
- Holm, S. (1979). "A simple sequentially rejective multiple test procedure." *Scand J Stat* 6:65. — Holm step-down.
- Politis, D. N., & Romano, J. P. (1994). "The Stationary Bootstrap." *J Am Stat Assoc* 89(428):1303. https://doi.org/10.1080/01621459.1994.10476870 — bootstrap base for Hansen/White.
