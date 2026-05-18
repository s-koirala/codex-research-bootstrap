---
name: mediation-analysis
description: Causal mediation analysis — decompose a total effect of X on Y into direct effect (X→Y not through M) and indirect/mediated effect (X→M→Y). Uses the VanderWeele 2014 counterfactual framework (natural direct/indirect effects) rather than the legacy Baron-Kenny product-of-coefficients approach. Cross-domain: epi (causal pathways for disease mechanisms), finance (intermediate variables in trading signal chains), biostats (mechanism-of-action studies).
---

# mediation-analysis

## When to invoke

You have a hypothesized causal pathway `X → M → Y` AND want to quantify how much of the total effect of X on Y operates through M versus directly (or through other unmeasured pathways). Examples:

- **Epi:** Does air pollution's effect on cardiovascular mortality act through inflammation (mediator)?
- **Finance:** Does a sentiment signal's effect on returns operate through volume changes (mediator), or directly via price?
- **Biostats:** What fraction of a drug's effect on outcome is mediated by biomarker change?

**Prerequisite:** the causal structure (DAG) must be declared first via [`dag-drafter`](../../.codex/agents/dag-drafter.toml). Mediation analysis on a misspecified DAG is meaningless.

## Frameworks (two — use the second)

### Legacy: Baron & Kenny 1986 product-of-coefficients

The classical 4-step approach ([^1]) regresses M on X, then Y on (X, M), and multiplies coefficients to get the indirect effect. **Do not use this as the primary framework** — it lacks a counterfactual interpretation, fails for nonlinear models or interactions, and provides no formal definition of "direct" vs "indirect" effect when X-M interaction is present.

Retained here only for backward-compatibility with legacy literature.

### Recommended: VanderWeele 2014 counterfactual framework

Natural direct effect (NDE) and natural indirect effect (NIE) defined via potential outcomes ([^2], [^3]):

- **NDE:** Effect of X on Y when M is held at the value it would naturally take under X=0.
- **NIE:** Effect on Y of changing M from its natural value under X=0 to its natural value under X=1.
- **Total effect (TE):** NDE + NIE (on the additive scale, under no X-M interaction).
- **Proportion mediated:** NIE / TE.

Identification requires four no-unmeasured-confounding assumptions ([^2] §2):
1. No unmeasured X-Y confounders (given covariates C)
2. No unmeasured M-Y confounders (given X and C)
3. No unmeasured X-M confounders (given C)
4. No M-Y confounder that is itself affected by X

The fourth assumption fails in many observational settings; sensitivity analysis is mandatory.

## Procedure

### 1. Specify the DAG

Via [`dag-drafter`](../../.codex/agents/dag-drafter.toml), include:
- Exposure X, Outcome Y, Mediator M
- Pre-exposure confounders C (affect any of X, M, Y but not affected by them)
- Post-exposure / intermediate variables explicitly excluded from the adjustment set (would violate assumption 4)

### 2. Fit the mediator model and outcome model

```python
# Mediator model: M | X, C
# Outcome model: Y | X, M, C
import statsmodels.api as sm
m_model = sm.OLS(df["M"], sm.add_constant(df[["X", "C1", "C2"]])).fit()
y_model = sm.OLS(df["Y"], sm.add_constant(df[["X", "M", "C1", "C2"]])).fit()
```

For binary Y use logit; for time-to-event Y use Cox; for binary M use logit and apply the appropriate transformation.

### 3. Compute NDE and NIE

Closed-form formulas (Valeri & VanderWeele 2013 [^4]) for linear models with potential X-M interaction:

```python
# For continuous Y, continuous M, no X-M interaction:
# beta1 = effect of X on M in m_model
# theta1 = effect of X on Y in y_model
# theta2 = effect of M on Y in y_model
# NDE = theta1
# NIE = beta1 * theta2
# TE = NDE + NIE
```

For interaction terms, use the closed-form NDE/NIE expressions from Valeri & VanderWeele 2013 §2.3-2.4 — these are NOT a simple coefficient product.

Alternatively, use a package:

```python
# Python: DoWhy or causal-inference packages
import dowhy
# R via rpy2: 'mediation' package (Tingley et al. 2014)
```

### 4. Bootstrap CIs for NDE and NIE

Asymptotic standard errors are not robust to nonlinearity. The canonical recommendation for mediation specifically is bias-corrected or percentile bootstrap (MacKinnon, Lockwood, Williams 2004 [^10]; Hayes 2009 [^11]), with B ≥ 1000 per general bootstrap convention (Davison & Hinkley 1997 [^5]):

```python
from sklearn.utils import resample
results = []
for _ in range(1000):  # justify: B=1000 community-canonical (Davison & Hinkley 1997 §2.5.1; Efron & Tibshirani 1993 §19)
    boot = resample(df, random_state=None)
    nde, nie = compute_effects(boot)
    results.append((nde, nie))
# Percentile CI: np.percentile(results, [2.5, 97.5], axis=0)
```

### 5. Sensitivity to unmeasured M-Y confounding

VanderWeele 2010 [^6] sensitivity parameter: compute the strength of unmeasured M-Y confounding (gamma, delta) needed to nullify NIE. Report as a bias-adjusted CI.

For epi: also compute E-value on the indirect effect (analogous to E-value for total effect; VanderWeele & Ding 2017 [^7]).

## Reporting

Report:
- DAG (with M role explicit)
- Pre-exposure confounders adjusted for
- NDE, NIE, TE (each with 95% bootstrap CI)
- Proportion mediated = NIE / TE (only meaningful when NDE and NIE have the same sign)
- Sensitivity analysis result
- Assumption 4 discussion (no intermediate confounders)

## Hand-off

- Pre-DAG: [`dag-drafter`](../../.codex/agents/dag-drafter.toml)
- Bootstrap implementation: [`statistical-analysis`](../statistical-analysis/SKILL.md) §"Time-series resample" + stationary bootstrap if M is autocorrelated
- E-value sensitivity: [`epi-auditor`](../../.codex/agents/epi-auditor.toml) mandatory check
- Output → [`deliver-results`](../deliver-results/SKILL.md)

## Cwd-specific notes

- **Epi cwd:** standard application; E-value mandatory.
- **Quant cwd:** sentiment → volume → return; volatility → liquidity → execution-cost; macroeconomic indicator → flow → spread. Treat indirect effect estimates as descriptive unless the no-unmeasured-confounder assumptions are seriously argued (rare in observational quant data; possible in event-study designs).

## References

[^1]: Baron, R. M., & Kenny, D. A. (1986). "The moderator-mediator variable distinction in social psychological research." *J Pers Soc Psychol* 51(6):1173-1182. https://doi.org/10.1037/0022-3514.51.6.1173 — legacy; do not use as primary.
[^2]: VanderWeele, T. J. (2014). "A unification of mediation and interaction: A 4-way decomposition." *Epidemiology* 25(5):749-761. https://doi.org/10.1097/EDE.0000000000000121
[^3]: VanderWeele, T. J. (2016). "Mediation analysis: A practitioner's guide." *Annu Rev Public Health* 37:17-32. https://doi.org/10.1146/annurev-publhealth-032315-021402
[^4]: Valeri, L., & VanderWeele, T. J. (2013). "Mediation analysis allowing for exposure-mediator interactions and causal interpretation: Theoretical assumptions and implementation with SAS and SPSS macros." *Psychol Methods* 18(2):137-150. https://doi.org/10.1037/a0031034
[^5]: Davison, A. C., & Hinkley, D. V. (1997). *Bootstrap Methods and their Application*. Cambridge University Press. ISBN 978-0521573917. §2.5.1.
[^6]: VanderWeele, T. J. (2010). "Bias formulas for sensitivity analysis for direct and indirect effects." *Epidemiology* 21(4):540-551. https://doi.org/10.1097/EDE.0b013e3181df191c
[^7]: VanderWeele, T. J., & Ding, P. (2017). "Sensitivity analysis in observational research: introducing the E-value." *Ann Intern Med* 167(4):268-274. https://doi.org/10.7326/M16-2607
[^8]: Tingley, D., Yamamoto, T., Hirose, K., Keele, L., & Imai, K. (2014). "mediation: R package for causal mediation analysis." *J Stat Softw* 59(5):1-38. https://doi.org/10.18637/jss.v059.i05
[^9]: DoWhy library (causal inference Python framework). https://www.pywhy.org/dowhy/
[^10]: MacKinnon, D. P., Lockwood, C. M., & Williams, J. (2004). "Confidence limits for the indirect effect: Distribution of the product and resampling methods." *Multivariate Behav Res* 39(1):99-128. https://doi.org/10.1207/s15327906mbr3901_4 — bootstrap is preferred over product-of-coefficients SEs for the indirect effect.
[^11]: Hayes, A. F. (2009). "Beyond Baron and Kenny: Statistical mediation analysis in the new millennium." *Communication Monographs* 76(4):408-420. https://doi.org/10.1080/03637750903310360 — bootstrap-based mediation framework.
