---
name: bayesian-workflow
description: Principled Bayesian inference pipeline — prior specification, prior-predictive checks, MCMC sampling, convergence diagnostics (R-hat, ESS, divergent transitions), posterior-predictive checks, and model comparison via LOO-CV. Follows the Gelman et al. 2020 "Bayesian Workflow" framework. Cross-domain: epi (hierarchical models for grouped data, weakly-informed priors for small studies), finance (regime-switching, time-varying volatility, structural breaks under uncertainty), biostats (random-effects meta-analysis, dose-response).
---

# bayesian-workflow

## When to invoke

Bayesian methods are appropriate when:

- **Domain priors are non-vacuous** and incorporating them improves inference (rare-disease, small-sample, regulated decision contexts).
- **Hierarchical structure** exists (patients within clinics; trades within strategies; observations within subjects) and partial pooling improves shrinkage.
- **Decision-theoretic interpretation** is needed (posterior probability that an effect exceeds a threshold; cost-weighted expected loss).
- **Posterior uncertainty** is the decision-relevant quantity, not a point estimate plus frequentist CI.

If a frequentist model is adequate and the data are large, use it. Bayesian computation costs (sampling time, convergence diagnostics, prior-sensitivity audits) are real.

## The workflow (Gelman et al. 2020)

This skill enforces the iterative workflow framework of Gelman, Vehtari, Simpson, et al. 2020 ([arXiv:2011.01808](https://arxiv.org/abs/2011.01808)) [^1]. The paper presents an iterative inspection-and-revision pattern (no fixed step count); the 8 enforcement gates this skill imposes are:

### 1. Prior specification

Three categories:
- **Weakly informative:** regularizes against extreme values; canonical default. Two well-supported choices:
  - **Cauchy(0, 2.5)** on standardized predictors (predictors scaled to mean 0, SD 0.5) — Gelman, Jakulin, Pittau, Su 2008 [^2] (the original recommendation for logistic regression).
  - **Normal(0, 2.5)** on standardized predictors — Stan-team current guidance [^9], adopted in many modern textbooks. Lighter-tailed than Cauchy; comparable regularization in most settings.
- **Informative:** justified by prior data or domain expert elicitation; document the source.
- **Flat / improper:** rarely appropriate; can cause sampling pathologies.

Document every prior with a `# justify:` comment naming the source (paper, prior-elicitation interview, regularization rationale).

### 2. Prior predictive check (mandatory before fitting)

Draw from the prior, simulate fake data, plot. Check that the simulated outcomes are plausible. If the prior produces outcomes 1000× larger than physically possible, the prior is wrong.

```python
import pymc as pm
import arviz as az
with pm.Model() as m:
    # Stan-team recommendation [^9] for standardized predictors; equivalent
    # rationale to Gelman 2008 Cauchy but lighter-tailed.
    beta = pm.Normal("beta", 0, 2.5)  # justify: stan-dev Prior-Choice-Recommendations wiki [^9]
    # HalfNormal scale 1 on standardized-residual scale per the same wiki.
    sigma = pm.HalfNormal("sigma", 1)  # justify: stan-dev Prior-Choice-Recommendations wiki [^9]
    y = pm.Normal("y", beta * x, sigma, observed=None)  # observed=None for prior check
    # Visualization-grade sample count for prior-predictive overlay; not
    # used for inference (Gelman 2020 §1.4).
    prior_pred = pm.sample_prior_predictive(samples=500)  # justify: ArviZ visualization default
az.plot_ppc(prior_pred)
```

### 3. Fit (MCMC)

Default: NUTS (No-U-Turn Sampler; Hoffman & Gelman 2014 [^3]) via PyMC or Stan. Configuration:

```python
with model:
    idata = pm.sample(
        draws=2000,        # justify: Gelman 2020 §3 recommends ≥1000 post-warmup; 2000 gives ESS headroom
        tune=2000,         # justify: Gelman 2020 §3 — tune ≥ draws for HMC adaptation
        chains=4,          # justify: ≥4 chains for rank-normalized split-R-hat per Vehtari et al. 2021 §4 [^4]
        target_accept=0.95,  # justify: Betancourt 2017 arXiv:1701.02434 recommends ≥0.95 for hierarchical / funnel geometries
        random_seed=42,    # justify: project convention; replace with the pre-registered seed from design.md §11
        return_inferencedata=True,
    )
```

### 4. Convergence diagnostics (mandatory)

Per Vehtari, Gelman, Simpson, Carpenter, Bürkner 2021 [^4]:

- **R-hat** (rank-normalized split-R-hat): must be < 1.01 for every parameter (Vehtari et al. 2021 [^4] §3.2). R-hat ≥ 1.01 → chains not converged; do not interpret posterior.
- **Effective sample size (bulk and tail):** ESS_bulk and ESS_tail ≥ 100 per chain (Vehtari et al. 2021 [^4] §4) — i.e., ≥ 400 with the default 4 chains — for reliable posterior summaries.
- **Divergent transitions:** zero. Any divergence indicates HMC posterior-geometry pathology — usually reparameterize (e.g., non-centered parameterization for hierarchical models).
- **E-BFMI** (Energy Bayesian Fraction of Missing Information): > 0.3 (HMC-specific; Betancourt 2018 arXiv:1604.00695 [^10] §6).

```python
print(az.summary(idata, var_names=["beta", "sigma"]))
# Inspect r_hat, ess_bulk, ess_tail columns.
print(idata.sample_stats.diverging.sum().item())  # divergences across chains
```

Halt the analysis if any of these fail. Diagnose:
- High R-hat → run more chains or longer; or model identification problem.
- Low ESS → autocorrelation in chains; reparameterize.
- Divergences → reparameterize (non-centered); increase `target_accept`; tighten priors.

### 5. Posterior predictive check (mandatory after fitting)

```python
with model:
    pp = pm.sample_posterior_predictive(idata)
# Visualization-grade overlay sample count; ArviZ default for plot_ppc readability.
az.plot_ppc(pp, num_pp_samples=100)  # justify: ArviZ plot_ppc visualization default
```

Simulated outcomes from the fitted model should resemble observed data. Systematic mismatch (e.g., model under-predicts the tail) indicates misspecification.

### 6. Sensitivity analysis (prior + likelihood)

- **Prior sensitivity:** refit with tighter and looser priors; report posterior shift. If the posterior moves substantially, the data are not pinning down the answer — disclose this.
- **Likelihood sensitivity:** refit with an alternative likelihood (e.g., Student-t instead of Normal for heavy-tailed residuals); report.

### 7. Model comparison

Leave-one-out cross-validation via Pareto-smoothed importance sampling (Vehtari, Gelman, Gabry 2017 [^5]):

```python
loo_a = az.loo(idata_a)
loo_b = az.loo(idata_b)
print(az.compare({"a": idata_a, "b": idata_b}))
```

Report ELPD difference with SE; differences < 2 SE are not strong evidence (Sivula, Magnusson, Vehtari 2022 arXiv:2008.10296 [^11]). Pareto k diagnostic > 0.7 for any observation → loo estimate unreliable for that case (Vehtari, Gelman, Gabry 2017 [^5] §2.2); use refit-leave-one-out for those points or report the issue.

### 8. Decision summary

Report:
- Posterior median + 95% credible interval (or HDI per Kruschke 2014 [^6])
- Posterior probability of decision-relevant claim (e.g., P(effect > 0))
- Sensitivity-analysis range
- Convergence diagnostics summary

## Anti-patterns to flag

- **No prior justification.** Every prior MUST cite either an elicitation source, a regularization rationale, or a published default.
- **Selective interpretation of credible intervals as if they were frequentist CIs.** Posterior probabilities are statements under the prior; do not interpret as objective frequencies.
- **Ignoring divergent transitions.** Even one divergence means the posterior geometry is misbehaving; the posterior summary may be biased.
- **Comparing models via DIC or AIC** instead of LOO or WAIC. DIC has known pathologies; use Pareto-smoothed importance sampling LOO.
- **Reporting a Bayes factor without prior justification.** BFs are highly prior-sensitive; specify and justify priors before computing.

## Hand-off

- Pre-data sample size: a "Bayesian power analysis" is computed via prior-predictive simulation (not the frequentist [`power-analysis`](../power-analysis/SKILL.md) formulas). Both can coexist depending on study design.
- Output → [`deliver-results`](../deliver-results/SKILL.md) for posterior-distribution figures (use `save_figure(target='single_col')` with ArviZ's plotting primitives).
- Reporting: epi work follows STROBE/TRIPOD; quant work follows the quant-cwd rule snippet.

## Cwd-specific notes

- **Epi cwd:** weakly-informative priors per Gelman 2008 are the default; refer to [`epi-auditor`](../../.codex/agents/epi-auditor.toml) for STROBE coverage of prior specification.
- **Quant cwd:** Bayesian state-space models (PyMC, NumPyro) for time-varying volatility (BSV) and regime-switching (Markov switching). Caveat: financial data are non-stationary; prior choice for hyperparameters matters.
- **Biostats:** hierarchical Bayes for random-effects meta-analysis (this skill complements [`meta-analysis`](../meta-analysis/SKILL.md)), dose-response (BUGS-era domain; now better in Stan/PyMC).

## References

[^1]: Gelman, A., Vehtari, A., Simpson, D., et al. (2020). "Bayesian Workflow." arXiv:2011.01808. https://arxiv.org/abs/2011.01808
[^2]: Gelman, A., Jakulin, A., Pittau, M. G., & Su, Y.-S. (2008). "A weakly informative default prior distribution for logistic and other regression models." *Ann Appl Stat* 2(4):1360-1383. https://doi.org/10.1214/08-AOAS191
[^3]: Hoffman, M. D., & Gelman, A. (2014). "The No-U-Turn Sampler: Adaptively setting path lengths in Hamiltonian Monte Carlo." *J Mach Learn Res* 15:1593-1623. http://www.jmlr.org/papers/v15/hoffman14a.html
[^4]: Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., & Bürkner, P.-C. (2021). "Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC." *Bayesian Analysis* 16(2):667-718. https://doi.org/10.1214/20-BA1221
[^5]: Vehtari, A., Gelman, A., & Gabry, J. (2017). "Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC." *Statistics and Computing* 27:1413-1432. https://doi.org/10.1007/s11222-016-9696-4
[^6]: Kruschke, J. K. (2014). *Doing Bayesian Data Analysis: A Tutorial with R, JAGS, and Stan*, 2nd ed. Academic Press. ISBN 978-0124058880.
[^7]: ArviZ documentation. https://python.arviz.org/
[^8]: PyMC documentation. https://www.pymc.io/
[^9]: Stan Development Team. "Prior Choice Recommendations" (wiki). https://github.com/stan-dev/stan/wiki/Prior-Choice-Recommendations — current Stan-team guidance for weakly-informative defaults; Normal(0, 2.5) on standardized predictors is the recommended logistic-regression default (lighter-tailed than the original Cauchy in Gelman 2008 [^2]).
[^10]: Betancourt, M. (2018). "A Conceptual Introduction to Hamiltonian Monte Carlo." arXiv:1604.00695. https://arxiv.org/abs/1604.00695 — §6 covers E-BFMI diagnostic.
[^11]: Sivula, T., Magnusson, M., & Vehtari, A. (2022). "Uncertainty in Bayesian leave-one-out cross-validation based model comparison." arXiv:2008.10296. https://arxiv.org/abs/2008.10296 — ELPD difference / SE rule of thumb.
