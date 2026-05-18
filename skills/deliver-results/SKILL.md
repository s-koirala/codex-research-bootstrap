---
name: deliver-results
description: Render the final-form figures, tables, Excel workbook, and report card for an analysis. Use whenever an analysis is ready to publish (paper figure, slide deck, stakeholder report, hypothesis disposition memo). Branches on cwd-matched rule file (quant vs epi) for the appropriate report-card template.
---

# deliver-results

## When to invoke

Use at the end of an analysis, when results are ready for downstream consumers:
publication figure, slide deck, stakeholder report, hypothesis disposition memo.

Skip for transient EDA — those plots are scratch, not deliverables.

## Pipeline

1. **Style figures via `publication.mplstyle`** — publication-grade defaults (font cascade, 300 dpi, Okabe-Ito 8-color, perceptually uniform colormaps). Single source of truth for matplotlib rcParams.
2. **Save with [save_figure.py](assets/save_figure.py)** — 3-format bundle (PNG@300dpi + SVG + PDF), `target=` keyword selects sizing (single_col / two_col / ppt_full / ppt_half / ppt_quad / print_600). Post-write `pdffonts` check verifies font embedding.
3. **Compile workbook via [workbook_skeleton.py](assets/workbook_skeleton.py)** — `xlsxwriter` writes the canonical 7-sheet layout: README → parameters → methods → results_* → figures → audit_trail → references. README sheet header captures the 13-field ReproLog envelope.
4. **Render report card** — branches on cwd-rule:
   - quant cwd → [report_card_quant.md](assets/report_card_quant.md). Sharpe is one KPI row among many, alongside survival-first KPIs (terminal-wealth-q05, Calmar, profit-factor, R-multiple, MaxDD, Sortino). Sharpe-CI methodology stays in the quant rule snippet, not inlined here.
   - epi cwd → [report_card_epi.md](assets/report_card_epi.md). YAML frontmatter selects reporting standard (STROBE/CONSORT/STARD/TRIPOD/PRISMA). Sections auto-fillable from `statistical-analysis` output JSON; PRISMA flow diagram externalized to PRISMA2020 Shiny.
5. **Log ReproLog** — every artifact emission goes through [emit-repro-log](../emit-repro-log/SKILL.md); ReproLog file referenced in commit trailers.

## Style parameters (in `publication.mplstyle`)

Every value cites a primary source — no magic numbers. Highlights:

| Param | Value | Source |
|---|---|---|
| `font.family` | DejaVu Sans → Liberation Sans → Arial → Helvetica | Matplotlib v2.0 default (release notes 2017-01-17); Liberation = Red Hat metric-Arial substitute; Nature/Science prefer Arial/Helvetica |
| `savefig.dpi` | 300 (raster default; bump to 600 via `target=print_600`) | Nature artwork guide: 300 dpi photograph/halftone min; 600 dpi line art / combination figures |
| `figure.figsize` | 3.5 x 2.7 (single-column) | Nature single-column = 89 mm = 3.50" |
| `pdf.fonttype` | 42 | TrueType embedding via PostScript Type 42 wrapper; editable in Illustrator |
| `image.cmap` | viridis | Perceptually uniform, colorblind-safe (van der Walt & Smith 2015; Kovesi 2015 arXiv:1509.03700) |
| `axes.prop_cycle` | Okabe-Ito 8-color | Wong 2011 *Nat Methods* 8:441 — colorblind-safe palette (distinct from matplotlib's tab10 which is Tableau-10) |

## Tabular outputs

- **Python summary tables (general):** `great_tables` (Iannone, Cheng, Schloerke). Render to both HTML (repo/web) and PNG@300dpi (slide embed).
- **Epi Table 1:** `tableone` (Pollard et al. 2018, *JAMIA Open* 1(1):26). Auto-covers STROBE item 14, CONSORT item 15, STARD items 19-20, TRIPOD 13b.
- **R workflow:** `gtsummary` for Table 1, `gt` for finalized tables.

**Storage convention (mandatory):** every table emits three siblings:
1. Source notebook at `notebooks/{topic}/build_{slug}.ipynb` — re-runnable
2. Frozen CSV at `artifacts/tables/{slug}_{YYYY-MM-DD}.csv` — canonical source of truth
3. Rendered HTML (web/repo) + PNG@300dpi (slide embed)

## Excel workbook

Use `xlsxwriter` (write-only; native chart object model; constant-memory mode for >1M rows). See [workbook_skeleton.py](assets/workbook_skeleton.py) for the 7-sheet canonical layout.

For round-tripping a user-supplied workbook, fall back to `openpyxl` ad-hoc — do not standardize on it for write paths.

## Slide-ready figure export

Standard sizes match Microsoft Office 16:9 defaults:
- `ppt_full`: 13.333" x 7.5"
- `ppt_half`: 6.5" x 7.5"
- `ppt_quad`: 6.5" x 3.5"

`save_figure(fig, slug, target="ppt_full")` produces PNG@300dpi default; SVG + PDF siblings always emitted. Programmatic deck assembly via `python-pptx` is out of scope for this skill; assemble manually from `artifacts/figures/`.

## Reporting standards

| Standard | When applies | Report card section that satisfies |
|---|---|---|
| STROBE | Observational studies | Items 1-22 in report_card_epi.md frontmatter selector |
| CONSORT 2010 | RCTs | Items 1-25 |
| STARD 2015 | Diagnostic accuracy | Items 1-32 |
| TRIPOD+AI 2024 | Prediction models | Items 1-27 |
| PRISMA 2020 | Systematic reviews | Flow diagram via PRISMA2020 Shiny |

For quant projects: no formal reporting standard. The `report_card_quant.md` template lists universe, splitter, KPIs, NW-HAC SE, diagnostics, and reproducibility appendix.

## Hand-off

- Consumes [emit-repro-log](../emit-repro-log/SKILL.md) — every artifact emission writes a ReproLog
- Consumes [validate-data](../validate-data/SKILL.md) — refuses to package output from a dataset that has not passed validation
- Hand-off to [audit-remediate-loop](../audit-remediate-loop/SKILL.md) when used inside that loop

## Critical compliance pins

- **Sharpe is reporting-only, never an optimization target.** The quant report card lists Sharpe as one row in a KPI table without elaboration; CI methodology stays in the quant rule snippet, not inlined here.
- **No magic numbers.** Every figure-size, DPI, font choice, and palette in `publication.mplstyle` has a primary-source citation in this SKILL.md.
- **Identity hygiene.** Generated artifacts never include real-name metadata. AI-assistance statements follow ICMJE 2026: model + role disclosure; AI tools cannot be authors.

## References

- Wong, B. (2011). "Points of view: Color blindness." *Nat Methods* 8:441. https://doi.org/10.1038/nmeth.1618
- Nuñez, J. R., Anderton, C. R., Renslow, R. S. (2018). "Optimizing colormaps with consideration for color vision deficiency." *PLoS One* 13:e0199239. https://doi.org/10.1371/journal.pone.0199239
- Crameri, F. et al. (2020). "The misuse of colour in science communication." *Nat Commun* 11:5444. https://doi.org/10.1038/s41467-020-19160-7
- Kovesi, P. (2015). "Good Colour Maps: How to Design Them." arXiv:1509.03700.
- Pollard, T. J. et al. (2018). "tableone." *JAMIA Open* 1(1):26. https://doi.org/10.1093/jamiaopen/ooy012
- Iannone, R., Cheng, J., Schloerke, B. *great_tables*. https://posit-dev.github.io/great-tables/
- Nature artwork guide: https://www.nature.com/documents/nature-final-artwork.pdf
- ICMJE Recommendations (updated January 2026): https://www.icmje.org/recommendations/
