#!/usr/bin/env python3
"""Build the manuscript reference.docx used by pandoc to style .md/.qmd -> .docx.

Generates `templates/manuscript/reference.docx` (relative to the bootstrap
repo root) with minimalist B&W styling that satisfies common major-journal
submission requirements (NEJM, JAMA, Lancet, BMJ, AJPH, Am J Epidemiol,
Ann Intern Med, JAMA Network):

- 12pt Times New Roman, double-spaced body
- 1-inch margins all sides
- Page numbers bottom-right
- Bold headings (same point size as body)
- No colors, no shading, no decorative formatting
- Standard styles: Title, Author, Heading 1-3, Body Text, Caption, Quote,
  List Paragraph, Footnote

Default output: <repo-root>/templates/manuscript/reference.docx. Override
with `--output <path>`.

Usage:
    python tools/build_manuscript_reference.py
    python tools/build_manuscript_reference.py --output path/to/reference.docx

Idempotent: re-running overwrites the reference doc. The user may further
customize in Word; re-running this script reverts customizations. Track
customizations in a separate doc (e.g., reference_custom.docx) if needed.

Specs derived from major clinical / medical / public-health journal
submission guidelines (consensus: 12pt Times New Roman, double-spaced,
1" margins).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_reference_docx(output_path: Path) -> Path:
    """Create the reference.docx via python-docx."""
    try:
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        print("ERROR: python-docx not installed. Run: uv pip install python-docx",
              file=sys.stderr)
        return Path()

    doc = Document()

    # --- Page setup: 1-inch margins all sides ---
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # --- Page numbers (bottom-right) ---
    # Add page number to footer via raw OOXML (python-docx lacks a high-level API).
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    fld_simple = OxmlElement("w:fldSimple")
    fld_simple.set(qn("w:instr"), "PAGE")
    run._r.append(fld_simple)

    # --- Define / override styles ---
    # justify: Times New Roman 12pt is the universal default for clinical
    # journal submission. NEJM, JAMA, Annals, AJPH, Am J Epidemiol all
    # specify 12pt Times New Roman explicitly. Lancet/BMJ accept Arial as
    # alternative; we ship Times to maximize compatibility.
    body_font = "Times New Roman"
    body_size = Pt(12)

    # Normal / Body Text style.
    normal = doc.styles["Normal"]
    normal.font.name = body_font
    normal.font.size = body_size
    normal.font.color.rgb = RGBColor(0, 0, 0)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    # justify: clinical journals overwhelmingly use block paragraphs
    # (no first-line indent) in submission manuscripts.
    pf.first_line_indent = Inches(0)

    # Headings (1, 2, 3): bold, same point size as body, double-spaced.
    for level in (1, 2, 3):
        style_name = f"Heading {level}"
        style = doc.styles[style_name]
        style.font.name = body_font
        style.font.size = body_size
        style.font.bold = True
        style.font.italic = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        pf = style.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
        pf.space_before = Pt(12)
        pf.space_after = Pt(0)

    # Title - distinct from body via size only; still B&W.
    # justify: one notch larger than body; matches Ann Intern Med
    # submission guideline (12-14pt title).
    title = doc.styles["Title"]
    title.font.name = body_font
    title.font.size = Pt(14)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    pf = title.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(0)
    pf.space_after = Pt(12)

    # Caption (for figures/tables).
    try:
        caption = doc.styles["Caption"]
    except KeyError:
        # Some Document instances don't pre-create Caption style.
        from docx.enum.style import WD_STYLE_TYPE
        caption = doc.styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    caption.font.name = body_font
    # justify: one notch smaller than body; matches AMA Manual of
    # Style figure caption guidance.
    caption.font.size = Pt(11)
    caption.font.bold = False
    caption.font.italic = False
    caption.font.color.rgb = RGBColor(0, 0, 0)
    pf = caption.paragraph_format
    # justify: captions single-spaced even when body is double;
    # AMA Manual of Style.
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)

    # Quote.
    try:
        quote = doc.styles["Quote"]
    except KeyError:
        from docx.enum.style import WD_STYLE_TYPE
        quote = doc.styles.add_style("Quote", WD_STYLE_TYPE.PARAGRAPH)
    quote.font.name = body_font
    quote.font.size = body_size
    # justify: clinical journals discourage italicized block quotes;
    # use indentation instead.
    quote.font.italic = False
    quote.font.color.rgb = RGBColor(0, 0, 0)
    pf = quote.paragraph_format
    pf.left_indent = Inches(0.5)
    pf.right_indent = Inches(0.5)
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)

    # List Paragraph.
    try:
        list_p = doc.styles["List Paragraph"]
        list_p.font.name = body_font
        list_p.font.size = body_size
        list_p.font.color.rgb = RGBColor(0, 0, 0)
        pf = list_p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    except KeyError:
        pass

    # Add a sentinel paragraph so pandoc finds at least one body paragraph
    # to derive from. Pandoc reference-doc convention: keep one Normal-style
    # paragraph; pandoc strips it when generating the actual output.
    doc.add_paragraph(
        "Reference doc - pandoc strips body content when rendering. "
        "Styles defined: Normal, Heading 1-3, Title, Caption, Quote, "
        "List Paragraph. Customize in Word if needed; re-running "
        "build_manuscript_reference.py reverts changes."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    default_out = repo_root / "templates" / "manuscript" / "reference.docx"

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--output", type=Path, default=default_out,
                   help=f"Output reference.docx path (default: {default_out.relative_to(repo_root).as_posix()})")
    args = p.parse_args(argv)

    out = args.output.resolve()
    result = build_reference_docx(out)
    if not result or not result.exists():
        print("FAIL: reference.docx not created", file=sys.stderr)
        return 1
    size_kb = result.stat().st_size / 1024
    print(f"PASS: reference.docx generated at {result} ({size_kb:.1f} KB)")
    print(f"  styles: Normal (12pt Times, double-spaced)")
    print(f"  margins: 1.0\" all sides")
    print(f"  page numbers: bottom-right")
    print(f"  colors: B&W only")
    print()
    print("Next: use with pandoc via tools/render_manuscript.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
