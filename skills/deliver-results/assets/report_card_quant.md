---
title: <<HID>> - <<TITLE>> - disposition memo
date: <<YYYY-MM-DD>>
type: disposition_memo
hypothesis_id: <<HID>>
status: <<ARCHIVE_NULL | PROMOTE | PARKED | UN_ARCHIVED>>
reporting_standard: quant-backtest (per project quant rule snippet)
substrate_dataset_checksum: <<sha256>>
sidecar: runs/<<HID>>/stage<<N>>/<<run_id>>/sidecar.json
sidecar_scientific_payload_sha256: <<sha256>>
git_head_at_authoring: <<short_sha>>
pip_freeze_sha256: <<sha256>>
rng_seed: <<int>>
ai_assistance: <<model+version>> (role=<<idea|code|prose|audit|multi>>; per ICMJE 2026)
---

# <<HID>> - <<TITLE>> - disposition memo

## 1. Universe and snapshot

| Field | Value |
|---|---|
| Instruments | <<e.g. ES, NQ front-month>> |
| Data vendor | <<vendor>> |
| Snapshot date | <<ISO>> |
| Survivorship-bias treatment | <<delisted-included / N/A for futures>> |
| Corporate-action adjustment | <<pre-applied / N/A>> |

## 2. Rebalance and execution

| Field | Value |
|---|---|
| Rebalance frequency | <<e.g. daily 09:30 ET>> |
| Transaction-cost model | <<bps fee + slippage; cite source>> |
| Capacity ceiling | <<contracts or notional; rationale>> |

## 3. Returns convention

| Field | Value |
|---|---|
| Return type | <<log | arithmetic>> |
| Compounding | <<continuous | simple>> |
| Funding/financing cost | <<applied | N/A>> |

## 4. Splitter

- **Type:** <<PurgedWalkForwardSplitter | CombinatorialPurgedCV (López de Prado AFML §7)>>
- **Train / val / test windows:** <<dates>>
- **Purge:** <<days>>
- **Embargo:** <<days>>

## 5. Headline performance (OOS test fold)

**Note:** Sharpe is a reporting KPI only, never an optimization target. Primary promotion gate is terminal-wealth-q05; Sharpe is one row among many. Sharpe-CI methodology lives in the project quant rule snippet, scoped to quant cwds.

| KPI | Value | Notes |
|---|---|---|
| Terminal-wealth-q05 | <<value>> | Survival-constrained tail; primary promotion gate |
| Calmar ratio | <<value>> | Annualized return / \|MaxDD\| |
| Profit factor | <<value>> | Gross gain / gross loss |
| R-multiple distribution | <<summary>> | Per-trade reward / risk; pre-cost |
| MaxDD | <<value>>% | Running peak-to-trough |
| MaxDD duration | <<bars>> | Time spent underwater |
| Sortino | <<value>> | Sortino & Price 1994 *J Investing* 3:59 |
| Sharpe (annualized) | <<value>> | KPI row only; CI methodology in project quant rule snippet |
| Deflated Sharpe | <<value>> | Bailey & López de Prado 2014 *J Portfolio Mgmt* 40(5):94 |
| PBO | <<value>> | Bailey et al. 2016 *J Comput Finance*; https://doi.org/10.21314/JCF.2016.322 |
| Turnover (annualized) | <<value>>x | Sum of \|Delta w\| annualized |
| Capacity estimate | <<USD or contracts>> | sqrt-impact at <<bps>> ADV |

## 6. Newey-West HAC standard errors

| Field | Value |
|---|---|
| Bandwidth selection | <<Newey & West 1994 data-dependent / Andrews 1991 plug-in>> |
| Selected lag | <<L>> |
| Kernel | <<Bartlett / QS>> |
| Prewhitening | <<yes / no>> |

## 7. Diagnostics

- Residual ACF (Ljung-Box p-value): <<value>>
- Return-distribution QQ vs Normal: <<value>>
- Return-distribution QQ vs Student-t: <<value>>
- Drawdown duration histogram: <<see figures>>
- Rolling 252-bar performance with bootstrap 95% band: <<see figures>>

## 8. Sensitivity

- Re-fit dropping top-5 leverage points: <<delta summary>>
- Alternative splitter (CPCV vs walk-forward): <<delta>>
- Block-bootstrap (Politis-Romano 1994 / Politis-White 2004 auto block length): <<delta>>

## 9. Disposition

**<<ARCHIVE_NULL | PROMOTE | PARKED | UN_ARCHIVED>>** per design.md section <<N>> strict-precedence tree.

Rationale: <<2-3 sentences>>

## 10. Reproducibility appendix

- Git HEAD at authoring: <<sha>>
- `uv pip freeze` SHA-256 (full 64-hex): <<sha>>
- Dataset SHA-256: <<sha>>
- RNG seed: <<int>>
- Model commit: <<sha>> or N/A
- ReproLog: `logs/reproducibility/repro_log_<<run_id>>.json`
- Pre-registration: `research/01_hypothesis_register/<<HID>>/design.md` SHA-256 = <<sha>>
- Substrate manifest: `data/_manifest.json`
- Sidecar JSON: `runs/<<HID>>/stage<<N>>/<<run_id>>/sidecar.json`

## 11. Author block

- Author: <<TODO: author name or pseudonym>>
- Affiliation: <<TODO: affiliation or N/A>>
- Contact: <<TODO: contact email or N/A>>
- Publication venue: <<TODO: project DOI host / preprint server / N/A>>
- DOI: <<TODO: project DOI>>

## 12. Failure log (append-only)

If status = ARCHIVE_NULL or PARKED, append to `research/01_hypothesis_register/<<HID>>/failure_log.md`. Never delete archived hypotheses (non-loss policy per project convention).
