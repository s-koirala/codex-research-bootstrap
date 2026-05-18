---
name: multiple-imputation
description: Multiple Imputation by Chained Equations (MICE) for missing data under the missing-at-random (MAR) assumption. Produces m complete datasets, runs the analysis on each, and pools estimates per Rubin's rules. Required by the population-health rule snippet when complete-case analysis is not appropriate. Cross-domain: epi (incomplete clinical records), finance (gappy market data series), biostats (any analysis on data with missingness).
---

# multiple-imputation

## When to invoke

Missingness is present AND complete-case analysis is biased OR inefficient. The decision tree:

| Missingness mechanism | Evidence | Treatment |
|---|---|---|
| **MCAR** (Missing Completely At Random) | Little's MCAR test p > 0.05 (pre-registered alpha; see Sterne et al. 2009 [^9] for guidance) AND domain rationale | Complete-case analysis acceptable |
| **MAR** (Missing At Random; conditional on observed) | Most realistic default | MICE (this skill) |
| **MNAR** (Missing Not At Random; depends on unobserved) | Domain rationale (e.g., dropout depends on outcome trajectory) | Pattern-mixture or selection models; MICE is biased |

Per the population-health rule snippet: "Declare MCAR/MAR/MNAR assumption with evidence. Primary analysis: multiple imputation with m ≥ percentage of incomplete cases (White, Royston, Wood 2011) unless MCAR is supported. Complete-case as sensitivity only."

## Procedure

### 1. Describe missingness

```python
# Per-variable missingness rate + pattern
df.isna().mean().sort_values()  # % missing per column
# Co-occurrence pattern matrix (which vars are missing together)
import missingno as msno
msno.matrix(df); msno.heatmap(df)
```

Report in the analysis doc:
- Per-variable missingness rate
- Total fraction of cases with any missingness (`(df.isna().any(axis=1)).mean()`)
- Patterns: monotone, arbitrary, time-clustered

### 2. State the missingness assumption with evidence

- **MCAR test:** Little 1988 [^1]. No standard statsmodels function ships this; in Python use `pyampute.exploration.mcar_statistical_tests.MCARTest` (or implement Little's χ² per Eq. 7 of [^1]); in R use `naniar::mcar_test()`. p > 0.05 is necessary but not sufficient — MCAR is rarely truly true.
- **MAR justification:** argue from data-collection mechanism (e.g., dropout was administrative, not outcome-driven) + show that imputation auxiliary variables capture the predictors of missingness.
- **MNAR concern:** if dropout/missingness depends on the unobserved value (e.g., high-income respondents refuse to disclose income), MICE is biased; use selection or pattern-mixture models instead.

### 3. Choose m

White, Royston, Wood 2011 [^2] rule: `m ≥ 100 × fraction-of-incomplete-cases` (rounded up).

Examples:
- 5% incomplete → m=5 (legacy default; minimum)
- 20% incomplete → m=20
- 50% incomplete → m=50  # justify: WRW 2011 §6.2 efficiency target

Older recommendations (m=3 or m=5) are not adequate when missingness is substantial — they inflate Monte Carlo error in the pooled estimate.

### 4. Run MICE

```python
# Python: statsmodels mice OR sklearn IterativeImputer
from statsmodels.imputation.mice import MICEData, MICE
import statsmodels.api as sm

mice_data = MICEData(df, perturbation_method="gaussian")
imp_model = MICE("Y ~ X1 + X2 + X3", sm.OLS, mice_data)
results = imp_model.fit(n_burnin=10, n_imputations=20)  # justify: WRW 2011 m≥%incomplete
print(results.summary())  # automatically pools via Rubin's rules
```

Or R (canonical):

```r
library(mice)
imp <- mice(df, m=20, method="pmm", seed=42, printFlag=FALSE)  # justify: m≥%incomplete
fit <- with(imp, lm(Y ~ X1 + X2 + X3))
pooled <- pool(fit)
summary(pooled)
```

### 5. Imputation model specification

- **Include the outcome** in the imputation model. Excluding it biases the analysis estimate (Moons et al. 2006 [^3]).
- **Include interactions and nonlinear terms** in the imputation model if they appear in the analysis model.
- **Auxiliary variables** (predictors of missingness or strong correlates of the missing variable, but not in the analysis model) should be included to improve imputation accuracy.
- **Predictive mean matching (PMM)** is the safe default for continuous variables (avoids distributional assumptions).
- **Logistic regression** for binary, multinomial for unordered categorical, proportional-odds for ordinal.

### 6. Diagnostics

- **Convergence:** trace plots of mean and SD of imputed values across iterations should mix; no trend.
- **Plausibility:** imputed values should be plausible relative to observed (e.g., no negative weights, no out-of-range systolic BPs).
- **Strip plots / density plots:** compare distribution of observed vs imputed for each variable; gross divergence suggests model misspecification.

```r
plot(imp)  # convergence
densityplot(imp)  # observed vs imputed densities
stripplot(imp)  # value-level comparison
```

### 7. Pool with Rubin's rules

The mice / statsmodels output handles this automatically:

- Point estimate: average of m estimates.
- Variance: within-imputation variance + (1 + 1/m) × between-imputation variance.
- Degrees of freedom: Barnard & Rubin 1999 [^4] small-sample correction.

### 8. Sensitivity analysis

- **Complete-case sensitivity:** run the same analysis on complete cases; report alongside MICE estimate. Large divergence is a signal — investigate the MAR assumption.
- **MNAR sensitivity:** δ-adjustment imputation (Carpenter & Kenward 2013 [^5]) — shift the imputed values by a fixed amount in the direction of unobserved bias and report how the estimate changes.
- **Tipping-point analysis** for binary outcomes: how extreme would the MNAR shift need to be to nullify the result?

## Reporting

For epi: STROBE [^6] item 12(c) covers missing data. CONSORT [^7] item 13(b) covers losses + exclusions. Report:
- Per-variable missingness rate
- MAR vs MNAR justification (qualitative + quantitative)
- m, imputation models, auxiliary variables
- Convergence diagnostics summary
- Pooled estimate with CI
- Complete-case sensitivity result

## Hand-off

- Pre-analysis: this skill runs BEFORE [`statistical-analysis`](../statistical-analysis/SKILL.md). Each of the m imputed datasets is then analyzed with the user's chosen method; pooling happens at the end.
- E-value sensitivity: required for any causal effect estimate even after MI (MICE does not address unmeasured confounding).
- Reporting: [`epi-auditor`](../../.codex/agents/epi-auditor.toml) audits MI methodology per the population-health rule snippet.

## Cwd-specific notes

- **Epi cwd:** standard application; common for cohort studies with dropout.
- **Quant cwd:** less common (most quant data is dense), but applicable to gappy alt-data series (irregular reporting cadence), corporate-events panels with selective reporting, and survey-based factor data. Caveat: MI on time-series can break temporal structure — use forward-fill or Kalman-smoother methods for series with autocorrelation.
- **Biostats cwd:** standard application.

## References

[^1]: Little, R. J. A. (1988). "A test of missing completely at random for multivariate data with missing values." *J Am Stat Assoc* 83(404):1198-1202. https://doi.org/10.1080/01621459.1988.10478722
[^2]: White, I. R., Royston, P., & Wood, A. M. (2011). "Multiple imputation using chained equations: Issues and guidance for practice." *Stat Med* 30(4):377-399. https://doi.org/10.1002/sim.4067
[^3]: Moons, K. G., Donders, R. A., Stijnen, T., & Harrell, F. E. (2006). "Using the outcome for imputation of missing predictor values was preferred." *J Clin Epidemiol* 59(10):1092-1101. https://doi.org/10.1016/j.jclinepi.2006.01.009
[^4]: Barnard, J., & Rubin, D. B. (1999). "Small-sample degrees of freedom with multiple imputation." *Biometrika* 86(4):948-955. https://doi.org/10.1093/biomet/86.4.948
[^5]: Carpenter, J. R., & Kenward, M. G. (2013). *Multiple Imputation and its Application*. Wiley. ISBN 978-0470740521. — δ-adjustment for MNAR.
[^6]: von Elm, E. et al. (2007). STROBE Statement. *PLOS Med* 4:e296. https://doi.org/10.1371/journal.pmed.0040296
[^7]: Schulz, K. F., Altman, D. G., Moher, D. (2010). CONSORT 2010. *BMJ* 340:c332. https://doi.org/10.1136/bmj.c332
[^8]: van Buuren, S., & Groothuis-Oudshoorn, K. (2011). "mice: Multivariate Imputation by Chained Equations in R." *J Stat Softw* 45(3):1-67. https://doi.org/10.18637/jss.v045.i03
[^9]: Sterne, J. A. C. et al. (2009). "Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls." *BMJ* 338:b2393. https://doi.org/10.1136/bmj.b2393
