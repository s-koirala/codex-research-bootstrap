---
name: render-manuscript
description: Render a manuscript markdown (.md/.qmd) to .docx via pandoc using the minimalist B&W reference.docx (12pt Times New Roman, double-spaced, 1" margins — major clinical/medical/public health journal compatible). Emits a render-log sidecar capturing input/output SHA-256 + pandoc version for reproducibility.
---

# render-manuscript

## Usage

```
render-manuscript <input.md> [-o <output.docx>] [--standard=<STROBE|CONSORT|STARD|TRIPOD|PRISMA>]
```

## Behavior

Run the render script with the supplied arguments:

```
python tools/render_manuscript.py <args>
```

Behavior:

1. Verify pandoc is on `PATH` (else print install instructions for Windows / macOS / Linux and exit 2).
2. Verify `templates/manuscript/reference.docx` exists (else instruct the user to run [tools/build_manuscript_reference.py](../../tools/build_manuscript_reference.py) once; exit 3).
3. Invoke pandoc:
   ```
   pandoc <input> -o <output.docx> --reference-doc <reference.docx> --standalone
   ```
4. Emit a sidecar `<output>.render.json` with input/output SHA-256 + pandoc version + reference.docx SHA — the replay anchor for the rendered doc.

## Reference.docx specifications

- 12pt Times New Roman body (universal across NEJM, JAMA, Lancet, BMJ, Ann Intern Med, AJPH, Am J Epidemiol).
- Double-spaced.
- 1" margins all sides.
- Page numbers bottom-right.
- Bold headings, same point size as body.
- Captions 11pt single-spaced (per AMA Manual of Style §4.2.3).
- Title 14pt bold center.
- No colors, no shading, no decorative formatting.

## Reporting-standard templates

Each available manuscript template carries the standard's checklist items embedded as HTML comments next to the corresponding section, so reviewers and submitters can audit completeness without leaving the manuscript:

- [templates/manuscript/manuscript_strobe_TEMPLATE.md](../../templates/manuscript/manuscript_strobe_TEMPLATE.md) — observational (STROBE 22-item).
- [templates/manuscript/manuscript_consort_TEMPLATE.md](../../templates/manuscript/manuscript_consort_TEMPLATE.md) — RCT (CONSORT 2010 25-item).
- [templates/manuscript/manuscript_stard_TEMPLATE.md](../../templates/manuscript/manuscript_stard_TEMPLATE.md) — diagnostic accuracy (STARD 2015 30-item).
- [templates/manuscript/manuscript_tripod_TEMPLATE.md](../../templates/manuscript/manuscript_tripod_TEMPLATE.md) — prediction model (TRIPOD+AI 2024 27-item).
- [templates/manuscript/manuscript_prisma_TEMPLATE.md](../../templates/manuscript/manuscript_prisma_TEMPLATE.md) — systematic review (PRISMA 2020 27-item).

## Identity hygiene

Per the identity-hygiene reminder in [AGENTS.md](../../AGENTS.md), the manuscript YAML frontmatter should carry whatever author identifier (pseudonym, project, or placeholder) the user has chosen for the publication — never a real-name email or affiliation. The reference.docx ships with empty `dc:creator` / `cp:lastModifiedBy` fields; `tools/render_manuscript.py` does not modify these.

## Customization

If a target journal has specific requirements not covered by the defaults (e.g., Lancet specifies Arial, BMJ requires line numbers), edit `templates/manuscript/reference.docx` in Word and save. Re-running `tools/build_manuscript_reference.py` reverts customizations; track venue-specific variants as `reference_<journal>.docx` siblings.

## References

- [Pandoc User's Guide — `--reference-doc`](https://pandoc.org/MANUAL.html#option--reference-doc).
- [python-docx](https://python-docx.readthedocs.io/) — the reference-doc generator.
- [AMA Manual of Style (11th ed.)](https://www.amamanualofstyle.com/) — figure/table caption typography.
- [ICMJE Recommendations (Jan 2026)](https://www.icmje.org/recommendations/) — manuscript preparation and AI-assistance disclosure.
