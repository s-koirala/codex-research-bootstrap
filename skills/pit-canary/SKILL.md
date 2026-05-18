---
name: pit-canary
description: Point-in-time leakage canary for backtest pipelines. Inject a known future-knowing feature; if it does NOT dominate the unmolested feature set, the pipeline already has a leak. Invoked by quant-auditor when reviewing quant backtests; standalone for the user via audit-loop. Cwd-scoped to quant projects.
---

# pit-canary

## When to invoke

Before any walk-forward run on time-series data, OR as part of `quant-auditor` review of a completed backtest. Quant-project cwd only (matches the quant-project rule snippet globs).

**Hand-off:** invoked by existing `quant-auditor`, NOT a new agent. `quant-auditor` already covers method-fidelity / leakage at the rule level.

## Canary pattern

The leakage taxonomy is grounded in López de Prado 2018 *Advances in Financial Machine Learning* §7 ("Cross-Validation in Finance"), which introduces purge + embargo as the structural defense against horizon-overlap leakage but does NOT itself prescribe the inject-the-future-feature canary technique. The three concrete canaries below are an operational diagnostic on top of the AFML §7 framework:

1. **Future-return-feature canary.** Inject the (t+1) realized return as a feature. Refit. If the injected feature does NOT win the permutation test against random-permutation null (i.e., is not detectably more important than chance), the pipeline already has a leak — some pre-existing feature encodes the future return through another channel. The discriminating statistic is the permutation p-value at the threshold below; the absolute-importance ratio is not load-bearing.
2. **Label-horizon-exceeds-purge canary.** Verify `label_horizon < purge` in the splitter. If `label_horizon >= purge`, training-set labels reach into validation-set features → information leak.
3. **HMM-fit-on-test canary** (if HMM regime layer is present). Verify the regime model was fit on TRAIN only, never on TEST. If the regime indicator improves OOS performance when fit on test, the regime layer is leaking.

## Test statistic

For canary 1 (future-return-feature):
- Permutation test, **n_perm = 1000**  # justify: Davison & Hinkley 1997 §2.5.1 + Efron & Tibshirani 1993 §19 — generic bootstrap-replicate convention. Politis-Romano 1994 introduces the stationary bootstrap but does not prescribe B; the B=1000 value is the community-canonical Monte-Carlo precision target.
- p-value threshold: **p < 0.01**  # justify: conservative because false negative = silent leak in production (high cost) and false positive = re-investigate (low cost). For a project-specific tighter or looser threshold, override in the project's `config/pit_canary.yaml`.
- Statistic: permutation-test feature importance (e.g., scikit-learn `permutation_importance`) of the injected future-feature, with the null being importance under random-label permutation.

Canary FAILS (i.e., LEAK DETECTED) if the future-feature does NOT dominate at p < 0.01 — meaning the unmolested pipeline already encodes the future return through some other channel.

## Procedure

1. **Locate the project's backtest config and feature set** (look for `config/hypotheses/<HID>.yaml` per project convention).
2. **Run baseline backtest** without injecting the canary.
3. **Inject canary 1** (future-return feature), refit, run baseline.
4. **Compute permutation importance** for the injected feature.
5. **Compute permutation p-value** (n_perm=1000) under the null that the injected feature is no more important than any randomly-permuted feature.
6. **Verify canaries 2 and 3** by inspecting the splitter config and HMM fit log.
7. **Write report** to `research/01_hypothesis_register/<HID>/pit_canary_{YYYY-MM-DD}.md`:
   ```markdown
   ---
   title: PIT canary report — <HID>
   date: <YYYY-MM-DD>
   hypothesis_id: <HID>
   type: pit_canary
   verdict: <PASS | FAIL>
   ---

   # PIT canary — <HID>

   ## Canary 1: future-return-feature
   - Injected feature: `return_t_plus_1`
   - Permutation importance ratio: <value>
   - Permutation p-value (n_perm=1000): <value>
   - Verdict: <PASS (p < 0.01) | FAIL (p >= 0.01 — leak detected)>

   ## Canary 2: label-horizon vs purge
   - `label_horizon`: <value>
   - `purge`: <value>
   - Verdict: <PASS (purge > label_horizon) | FAIL>

   ## Canary 3: HMM-fit-on-test (if applicable)
   - Fit window: <value>
   - Test window: <value>
   - Verdict: <PASS | FAIL | N/A>

   ## Overall: <PASS | FAIL>
   ```
8. **Emit ReproLog** with `phase=validation`, `hypothesis_id=<HID>`, `rng_seed=<seed used for permutation>`, `config_resolved_sha256=<pit_canary report SHA>`.
9. **If any canary FAILS:** raise to `audit-remediate-loop` as a `critical` finding. Quant-auditor blocks the run; user must fix the leak before proceeding.

## Necessary, not sufficient

PIT canaries detect *some* forms of look-ahead bias but cannot prove the pipeline is leak-free. Pair with:
- `quant-auditor` review of feature lag operators
- Code review of any feature using `pd.shift` or `rolling`
- Visual inspection of feature/label timestamp distributions

## Hand-off

- Invoked by [`quant-auditor`](../../.codex/agents/quant-auditor.toml) when reviewing quant backtests.
- Reports emit ReproLog via [emit-repro-log](../emit-repro-log/SKILL.md).
- Failures escalate to [`audit-remediate-loop`](../audit-remediate-loop/SKILL.md) as critical findings.

## References

- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. ISBN 978-1119482086. §7 "Cross-Validation in Finance" — introduces purge + embargo as the structural defense against horizon-overlap leakage. §8.3 covers permutation importance for ML pipelines.
- Davison, A. C., & Hinkley, D. V. (1997). *Bootstrap Methods and their Application*. Cambridge University Press. ISBN 0-521-57391-2. §2.5.1 — B=1000 bootstrap-replicate convention.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall. ISBN 0-412-04231-2. §19 — Monte-Carlo precision targets for permutation tests.
- Good, P. I. (2005). *Permutation, Parametric, and Bootstrap Tests of Hypotheses*, 3rd ed. Springer. ISBN 978-0387200279. Ch. 3 — permutation-test p-value Monte-Carlo precision.
