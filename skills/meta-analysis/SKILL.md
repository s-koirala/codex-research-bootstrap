---
name: meta-analysis
description: Quantitative synthesis of multiple studies — random-effects (DerSimonian-Laird default; Hartung-Knapp-Sidik-Jonkman correction for small k), fixed-effects, heterogeneity assessment via I² and Cochran's Q, publication-bias diagnostics via funnel plot + Egger test, and forest plot rendering. Pairs with the PRISMA 2020 reporting standard; this skill is the analytic engine the PRISMA review uses.
---

# meta-analysis

## When to invoke

Multiple primary studies report estimates of the same effect AND the goal is a pooled estimate with uncertainty plus assessment of between-study heterogeneity and publication bias. This skill produces the analytic content for a systematic review; the PRISMA manuscript template (`templates/manuscript/manuscript_prisma_TEMPLATE.md`) is the report wrapper.

## Procedure

### 1. Tabulate effect sizes

For each included study, extract:
- Effect estimate (Hedges' g, log-OR, log-HR, mean difference, correlation z-transform, etc.)
- Standard error (or 95% CI from which SE is derived)
- Sample size
- Study characteristics for moderator analysis (year, design, population, intervention)

Effect-size conversion formulas: Borenstein et al. 2009 [^1] Ch. 4-7. Use established conversion (e.g., log-OR from 2×2 table; Hedges' g from t-test).

### 2. Choose the model

| Model | When | Reference |
|---|---|---|
| **Fixed-effects** | Studies estimate a common true effect (rare in practice) | Hedges & Olkin 1985 [^2] |
| **Random-effects (DerSimonian-Laird)** | True effects vary; canonical default | DerSimonian & Laird 1986 [^3] |
| **Random-effects (REML)** | Better small-k properties; default in metafor | Viechtbauer 2005 [^4] |
| **Hartung-Knapp-Sidik-Jonkman (HKSJ)** | Small k (IntHout, Ioannidis, Borm 2014 simulated k = 5–50 and found HKSJ outperforms DL throughout); maintains nominal coverage where DL is anti-conservative | IntHout, Ioannidis, Borm 2014 [^5] |
| **Bayesian random-effects** | Want a posterior on τ²; informative priors on heterogeneity | Higgins, Thompson, Spiegelhalter 2009 [^6] + this skill's [`bayesian-workflow`](../bayesian-workflow/SKILL.md) |

**Default for clinical/medical/public-health meta-analyses (small to moderate k):** REML with Hartung-Knapp adjustment. The DerSimonian-Laird random-effects model is anti-conservative when k is small.

### 3. Fit

```r
# R (canonical; Viechtbauer 2010 metafor)
library(metafor)
res <- rma(yi=effect, sei=se, data=studies, method="REML", test="knha")  # justify: HKSJ for small k
print(res)
forest(res)
funnel(res)
```

```python
# Python alternatives
# 1. statsmodels.stats.meta_analysis (DL fixed/random)
from statsmodels.stats.meta_analysis import combine_effects
res = combine_effects(effect, var, method_re="dl", row_names=studies)
print(res.summary_frame())

# 2. PyMeta (more comprehensive)
# 3. Or call R via rpy2 for full metafor parity
```

### 4. Heterogeneity assessment

- **Cochran's Q** (Cochran 1954 [^7]): test of homogeneity; null is "all true effects equal." p-value sensitive to k; do not over-interpret.
- **I²** (Higgins & Thompson 2002 [^8]): percentage of total variation due to between-study heterogeneity rather than sampling error. Treat as descriptive, not a hypothesis test. The widely-used categorization (0-25% low, 25-50% moderate, 50-75% substantial, >75% considerable) is from the Cochrane Handbook §10.10.2 [^17]; Higgins & Thompson 2002 itself cautions against fixed I² thresholds.
- **τ²:** between-study variance estimate. Report alongside I². For Bayesian models, report posterior distribution of τ.
- **Prediction interval:** the range within which a future study's true effect is expected to fall (IntHout et al. 2016 [^9]) — more useful than the CI for the pooled estimate alone.

### 5. Publication-bias diagnostics

- **Funnel plot** (Light & Pillemer 1984 [^10]): scatter of effect size vs. SE. Asymmetry suggests publication bias.
- **Egger's test** (Egger, Davey Smith, Schneider, Minder 1997 [^11]): linear regression of standardized effect on precision. p < 0.10 (the 0.10 threshold is conventional in subsequent literature — Sterne & Egger 2001 [^18] and Cochrane Handbook §13.3.5.4 [^17] — not in the original 1997 paper; chosen due to low power of the test) suggests asymmetry. NOT reliable for k < 10.
- **Trim-and-fill** (Duval & Tweedie 2000 [^12]): imputes missing studies on the funnel-plot opposite side and re-estimates the pooled effect. Use as sensitivity, not as primary estimate.
- **PET-PEESE** (Stanley & Doucouliagos 2014 [^13]): regression-based adjustment for small-study effects.

### 6. Moderator (meta-regression) analysis

If heterogeneity is non-negligible (I² > 50%), explore moderators:

```r
res_mod <- rma(yi=effect, sei=se, mods=~ year + population, data=studies, method="REML")
print(res_mod)
```

Pre-register moderators in `docs/protocol/protocol_v0.md` per PRISMA item 13c; do not data-dredge.

### 7. Sensitivity

- **Leave-one-out:** refit dropping each study in turn; assess influence.
- **Risk-of-bias subgroup:** if studies were rated for risk-of-bias (RoB 2 for RCTs, ROBINS-I for observational), pool low-RoB studies separately.
- **Outlier diagnostics:** Cook's distance, hat values per metafor (`influence(res)`).

### 8. Forest plot rendering

```r
forest(res, slab=studies$id, header=TRUE)
```

Or via [`deliver-results`](../deliver-results/SKILL.md) `save_figure(target='single_col')` after building a custom matplotlib forest plot.

## Reporting (PRISMA 2020)

Output is consumed by the PRISMA manuscript template (`templates/manuscript/manuscript_prisma_TEMPLATE.md`). Item-level coverage:

- PRISMA item 13(b) (synthesis methods): document model, software, heterogeneity statistic
- 13(d) (heterogeneity): I², τ², prediction interval
- 13(e) (subgroup/moderator): pre-registered subgroup analyses
- 14 (reporting-bias methods): funnel + Egger
- 20 (synthesis results): pooled estimate + 95% CI + 95% PI
- 21 (reporting bias): funnel-plot + Egger + trim-and-fill if applicable
- 22 (certainty): GRADE assessment

## Hand-off

- Upstream: [`validate-data`](../validate-data/SKILL.md) on the extracted-effects table (per-study row sanity-checks).
- Downstream: [`deliver-results`](../deliver-results/SKILL.md) for forest plot + funnel plot; the PRISMA manuscript template wraps the analysis results.
- For Bayesian random-effects: [`bayesian-workflow`](../bayesian-workflow/SKILL.md).
- Reporting standard: PRISMA 2020 ([Page et al. 2021 BMJ 372:n71](https://doi.org/10.1136/bmj.n71)).

## Cwd-specific notes

- **Epi cwd:** standard application; usually clinical or observational.
- **Quant cwd:** less common but applicable to "meta-analysis of strategies" (pooled Sharpe? — note Sharpe is reporting-only per the quant-cwd rule snippet; use survival-constrained KPIs instead). Better fit for pooling factor exposures across strategy variants or replication-attempt meta-analyses.
- **Biostats:** dose-response meta-analysis, individual-participant-data (IPD) meta-analysis — these are extensions not fully covered by this skill; consult Riley, Tierney, Stewart 2021 [^14] for IPD-MA methodology.

## References

[^1]: Borenstein, M., Hedges, L. V., Higgins, J. P. T., & Rothstein, H. R. (2009). *Introduction to Meta-Analysis*. Wiley. ISBN 978-0470057247.
[^2]: Hedges, L. V., & Olkin, I. (1985). *Statistical Methods for Meta-Analysis*. Academic Press. ISBN 978-0123363800.
[^3]: DerSimonian, R., & Laird, N. (1986). "Meta-analysis in clinical trials." *Controlled Clinical Trials* 7(3):177-188. https://doi.org/10.1016/0197-2456(86)90046-2
[^4]: Viechtbauer, W. (2005). "Bias and efficiency of meta-analytic variance estimators in the random-effects model." *J Educ Behav Stat* 30(3):261-293. https://doi.org/10.3102/10769986030003261
[^5]: IntHout, J., Ioannidis, J. P. A., & Borm, G. F. (2014). "The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method." *BMC Med Res Methodol* 14:25. https://doi.org/10.1186/1471-2288-14-25
[^6]: Higgins, J. P. T., Thompson, S. G., & Spiegelhalter, D. J. (2009). "A re-evaluation of random-effects meta-analysis." *J R Stat Soc A* 172(1):137-159. https://doi.org/10.1111/j.1467-985X.2008.00552.x
[^7]: Cochran, W. G. (1954). "The combination of estimates from different experiments." *Biometrics* 10(1):101-129. https://doi.org/10.2307/3001666
[^8]: Higgins, J. P. T., & Thompson, S. G. (2002). "Quantifying heterogeneity in a meta-analysis." *Stat Med* 21(11):1539-1558. https://doi.org/10.1002/sim.1186
[^9]: IntHout, J., Ioannidis, J. P. A., Rovers, M. M., & Goeman, J. J. (2016). "Plea for routinely presenting prediction intervals in meta-analysis." *BMJ Open* 6(7):e010247. https://doi.org/10.1136/bmjopen-2015-010247
[^10]: Light, R. J., & Pillemer, D. B. (1984). *Summing Up: The Science of Reviewing Research*. Harvard University Press. ISBN 978-0674854314.
[^11]: Egger, M., Davey Smith, G., Schneider, M., & Minder, C. (1997). "Bias in meta-analysis detected by a simple, graphical test." *BMJ* 315(7109):629-634. https://doi.org/10.1136/bmj.315.7109.629
[^12]: Duval, S., & Tweedie, R. (2000). "Trim and fill: A simple funnel-plot-based method of testing and adjusting for publication bias in meta-analysis." *Biometrics* 56(2):455-463. https://doi.org/10.1111/j.0006-341X.2000.00455.x
[^13]: Stanley, T. D., & Doucouliagos, H. (2014). "Meta-regression approximations to reduce publication selection bias." *Res Synth Methods* 5(1):60-78. https://doi.org/10.1002/jrsm.1095
[^14]: Riley, R. D., Tierney, J. F., & Stewart, L. A. (Eds.) (2021). *Individual Participant Data Meta-Analysis: A Handbook for Healthcare Research*. Wiley. ISBN 978-1119333722.
[^15]: Viechtbauer, W. (2010). "Conducting meta-analyses in R with the metafor package." *J Stat Softw* 36(3):1-48. https://doi.org/10.18637/jss.v036.i03
[^16]: Page, M. J. et al. (2021). "The PRISMA 2020 statement: an updated guideline for reporting systematic reviews." *BMJ* 372:n71. https://doi.org/10.1136/bmj.n71
[^17]: Higgins, J. P. T., Thomas, J., Chandler, J., Cumpston, M., Li, T., Page, M. J., Welch, V. A. (Eds.). *Cochrane Handbook for Systematic Reviews of Interventions*, version 6.4 (2023). §10.10.2 (I² interpretation thresholds) and §13.3.5.4 (Egger test conventions). https://training.cochrane.org/handbook
[^18]: Sterne, J. A. C., & Egger, M. (2001). "Funnel plots for detecting bias in meta-analysis: guidelines on choice of axis." *J Clin Epidemiol* 54(10):1046-1055. https://doi.org/10.1016/S0895-4356(01)00377-8 — sets the convention for the 0.10 Egger threshold.
