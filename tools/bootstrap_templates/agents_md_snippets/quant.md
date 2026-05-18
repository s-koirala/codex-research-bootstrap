# Quant-project rules

This snippet is installed as a per-subdirectory `AGENTS.md` (or appended to
the project root `AGENTS.md`) by `tools/bootstrap_project.py --kind quant`.
Codex walks from the git root to the current working directory and
concatenates each `AGENTS.md` it encounters, so this content activates by
path: it applies whenever Codex is operating inside a project whose cwd
matches one of the globs below.

**Apply when cwd matches any of:** `**/backtest*/`, `**/factor*/`,
`**/signal*/`, `**/strategy*/`.

If cwd does not match, ignore this section entirely.

## Time-series integrity

- **No look-ahead.** Every feature must be computable at time t using only
  data available at time t.
- **Time-ordered splits.** Train/val/test splits are time-ordered and
  disjoint. Walk-forward cross-validation, never k-fold.
- **Returns.** State log vs. arithmetic and the compounding convention at
  the top of the analysis.
- **Prices.** Adjust for corporate actions before any return calculation.

## Inference

- **Standard errors.** Newey-West (HAC) with data-dependent bandwidth
  selection per
  [Newey & West 1994, DOI 10.2307/2297912](https://doi.org/10.2307/2297912),
  or the Andrews parametric plug-in per
  [Andrews 1991, DOI 10.2307/2938229](https://doi.org/10.2307/2938229).
- **Sharpe confidence intervals.** Report a bootstrap CI on Sharpe. For
  single-strategy CIs use
  [Opdyke 2007, DOI 10.1057/palgrave.jam.2250084](https://doi.org/10.1057/palgrave.jam.2250084)
  or the asymptotic CI of
  [Lo 2002, DOI 10.2469/faj.v58.n4.2453](https://doi.org/10.2469/faj.v58.n4.2453).
  For pairwise strategy comparison use the studentized time-series
  bootstrap of
  [Ledoit & Wolf 2008, DOI 10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002).
- **Multiple testing across strategies.** White's reality check
  ([White 2000, DOI 10.1111/1468-0262.00152](https://doi.org/10.1111/1468-0262.00152))
  or Hansen's SPA
  ([Hansen 2005, DOI 10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063)).

## Reporting

Every backtest document lists:

- Universe.
- Rebalance frequency.
- Transaction-cost model.
- Survivorship-bias treatment.
- Data vendor + snapshot date.

Plus the performance-metric set:

- Sharpe.
- Sortino.
- Maximum drawdown.
- Turnover.
- Capacity estimate.

## Published research

Any factor, signal, or rule must have a citation or a derivation. No
unattributed folklore factors.
