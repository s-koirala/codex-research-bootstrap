---
name: survival-analysis
description: Time-to-event analysis — Kaplan-Meier survival curves, log-rank tests, Cox proportional-hazards regression, accelerated-failure-time (AFT) models, and proportional-hazards assumption diagnostics via scaled-Schoenfeld residuals. Cross-domain: finance (time-to-default, drawdown duration, position holding time), epi (mortality, recurrence, discharge), biostatistics (any duration outcome). Invoke whenever the dependent variable is a time interval ending in an event (with possible censoring).
---

# survival-analysis

## When to invoke

The dependent variable is a time interval until an event of interest, with the possibility of right-censoring (event not observed by end of follow-up). Examples:

- **Finance:** time-to-default on a portfolio of bonds; time-to-trade-exit for a strategy; drawdown duration; time-to-margin-call.
- **Epidemiology:** mortality, hospital readmission, time-to-recurrence, time-to-treatment-discontinuation.
- **Biostatistics:** any time-to-event outcome with censoring.

Do NOT use OLS regression on duration outcomes with censoring — censored observations are partial information, and dropping them or imputing the end of follow-up biases the estimate. Survival models handle censoring correctly.

## Procedure

### 1. Frame the question

- **Estimand:** survival function `S(t) = P(T > t)`, hazard `h(t) = lim_{Δt→0} P(t ≤ T < t+Δt | T ≥ t) / Δt`, or cumulative hazard `H(t)`.
- **Event definition:** what counts as the event? When does follow-up start (`t=0` anchor)?
- **Censoring type:** right-censored (most common; observation ends before event), left-truncated (entry after `t=0`; e.g., delayed entry into a cohort), or interval-censored (event known only to be within an interval).

### 2. Non-parametric estimate: Kaplan-Meier

```python
from lifelines import KaplanMeierFitter
kmf = KaplanMeierFitter()
kmf.fit(durations=df["duration"], event_observed=df["event"])
kmf.plot_survival_function()
```

Reference: Kaplan & Meier 1958 [^1]. Use for unconditional survival curves stratified by group; pair with a **log-rank test** ([^2]) for between-group comparison:

```python
from lifelines.statistics import logrank_test
r = logrank_test(durations_A, durations_B, event_observed_A, event_observed_B)
print(r.p_value, r.test_statistic)
```

### 3. Semi-parametric: Cox proportional-hazards regression

For covariate adjustment:

```python
from lifelines import CoxPHFitter
cph = CoxPHFitter()
cph.fit(df, duration_col="duration", event_col="event")
print(cph.summary)
```

Reference: Cox 1972 [^3]. The proportional-hazards assumption (covariate effects are constant over time) must be tested — do NOT assume.

### 4. Proportional-hazards assumption check (mandatory)

Scaled Schoenfeld residuals per Grambsch & Therneau 1994 [^4]:

```python
cph.check_assumptions(df, p_value_threshold=0.05)  # justify: pre-registered alpha; reduce if multiple tests
```

If the test rejects PH for a covariate:
- **Stratify** on that covariate (allow separate baseline hazard per stratum).
- **Time-varying coefficient:** fit a Cox model with `cox_with_varying_coefficients` or use a different parameterization.
- **Switch to AFT model** (accelerated failure time; covariate-on-log-time instead of covariate-on-log-hazard).

### 5. AFT alternative

When the PH assumption fails badly OR when an absolute-time interpretation is more useful than a hazard-ratio one, use a parametric AFT model (log-normal, Weibull, log-logistic):

```python
from lifelines import WeibullAFTFitter
aft = WeibullAFTFitter()
aft.fit(df, duration_col="duration", event_col="event")
```

Reference: Wei 1992 [^5]; Therneau & Grambsch 2000 [^6].

### 6. Diagnostics

- **Schoenfeld residuals vs time** — flat line indicates PH satisfied; trend indicates violation.
- **Martingale residuals vs covariate** — detects functional-form misspecification (non-linearity).
- **Deviance residuals** — outliers in the time-to-event scale.
- **DFBETAS per covariate** — influence of individual observations on each coefficient.
- **Concordance index (Harrell's C)** — discrimination ability; analogous to AUC for survival data; for a Cox model, output from `cph.concordance_index_`.

### 7. Reporting

For epi: TRIPOD+AI [^7] item 15 (discrimination + calibration) applies to prognostic prediction models. For trials: CONSORT [^8] item 17. Report:
- Number of events / total n
- Median follow-up
- Kaplan-Meier curves with 95% CI bands
- Hazard ratio (or AFT time ratio) with 95% CI
- PH-assumption test result for every covariate
- Concordance index

## Hand-off

- Output → [`deliver-results`](../deliver-results/SKILL.md) for figures (Kaplan-Meier survival curve via `save_figure(target='two_col')`) and report card.
- Pre-data sample size: use [`power-analysis`](../power-analysis/SKILL.md) with Schoenfeld's formula for log-rank test (effective sample size = number of events, not n participants).
- Multiple-testing across subgroups: [`multipletest-gate`](../multipletest-gate/SKILL.md).

## Cwd-specific notes

- **Quant cwd** (quant-project rule snippet): time-to-default, time-to-stop-loss, position holding-time analysis. Survival data with finance-specific censoring (e.g., end-of-sample) is mathematically identical to medical censoring.
- **Epi cwd** (population-health rule snippet): mandatory E-value sensitivity for any causal HR claim (VanderWeele & Ding 2017; applied to the hazard ratio scale). DAG-derived adjustment set via [`dag-drafter`](../../.codex/agents/dag-drafter.toml) before specifying the Cox model.

## References

[^1]: Kaplan, E. L., & Meier, P. (1958). "Nonparametric estimation from incomplete observations." *J Am Stat Assoc* 53(282):457-481. https://doi.org/10.1080/01621459.1958.10501452
[^2]: Mantel, N. (1966). "Evaluation of survival data and two new rank order statistics arising in its consideration." *Cancer Chemotherapy Reports* 50(3):163-170. (Log-rank test; also Peto & Peto 1972.)
[^3]: Cox, D. R. (1972). "Regression models and life-tables." *J R Stat Soc B* 34(2):187-202 (with discussion 202-220). https://doi.org/10.1111/j.2517-6161.1972.tb00899.x
[^4]: Grambsch, P. M., & Therneau, T. M. (1994). "Proportional hazards tests and diagnostics based on weighted residuals." *Biometrika* 81(3):515-526. https://doi.org/10.1093/biomet/81.3.515
[^5]: Wei, L. J. (1992). "The accelerated failure time model: a useful alternative to the Cox regression model in survival analysis." *Stat Med* 11(14-15):1871-1879. https://doi.org/10.1002/sim.4780111409
[^6]: Therneau, T. M., & Grambsch, P. M. (2000). *Modeling Survival Data: Extending the Cox Model*. Springer. ISBN 978-0387987842.
[^7]: Collins, G. S. et al. (2024). "TRIPOD+AI statement." *BMJ* 385:e078378. https://doi.org/10.1136/bmj-2023-078378
[^8]: Schulz, K. F., Altman, D. G., Moher, D. (2010). "CONSORT 2010 Statement." *BMJ* 340:c332. https://doi.org/10.1136/bmj.c332
[^9]: Davidson-Pilon, C. (2019). "lifelines: survival analysis in Python." *JOSS* 4(40):1317. https://doi.org/10.21105/joss.01317
