---
name: cite-add
description: Resolve a DOI or URL via CrossRef MCP and append the parsed citation to the project's CITATION.cff `references:` list.
---

# cite-add

## Usage

```
cite-add <DOI | URL>
```

## Behavior

Resolve the argument via the `crossref` MCP server and append a CFF v1.2.0 reference entry to the project's `CITATION.cff`. Steps:

1. Locate `CITATION.cff` at the project root. If absent, error with:
   > "No CITATION.cff at project root. Run the `bootstrap-project` skill or copy from `templates/CITATION.cff.tmpl`."

2. Normalize input: strip whitespace; accept either a bare DOI (e.g. `10.1093/jamiaopen/ooy012`), a DOI URL (e.g. `https://doi.org/10.1093/...`), or a CrossRef API URL. Extract the DOI portion.

3. Call the `crossref` MCP server's lookup tool (h-lu/crossref-cite-mcp) with the DOI. Request CSL-JSON output. If MCP unavailable, fall back to a direct HTTPS GET to `https://api.crossref.org/works/{doi}` (User-Agent must include `$CROSSREF_MAILTO` per CrossRef polite-pool policy).

4. Parse the response. Extract:
   - `authors`: list of `{family, given}` from CSL `author` array.
   - `title`: first element of CSL `title` array.
   - `year`: `issued.date-parts[0][0]`.
   - `journal` / `container-title`: CSL `container-title` (or `publisher` for books).
   - `volume`, `issue`, `page` (if present).
   - `doi`: the resolved DOI.
   - `type`: CSL `type` mapped to CFF reference type (e.g. `journal-article` → `article`; `book` → `book`; `proceedings-article` → `conference-paper`).

5. Build a CFF v1.2.0 reference dict. Required CFF reference fields:
   - `type` (e.g. `article`)
   - `authors` (list of `{family-names, given-names}`)
   - `title`
   - `year`
   - `doi`

6. Append to the existing `references:` list in `CITATION.cff`. If the file's `references` is missing or `[]`, replace with the new list. Preserve YAML key order and comments where possible (use `ruamel.yaml` round-trip if available; otherwise re-write with PyYAML and warn that comments may be lost).

7. Verify by re-running `python hooks/precommit_citation_cff.py CITATION.cff` — must exit 0.

8. Report: print the appended reference (short form: `Added: <first author> et al. (<year>) <title> <doi>`) and the path to the modified file.

## Identity hygiene

Per the contributor identity-hygiene reminder in [AGENTS.md](../../AGENTS.md), never substitute a real-name email or affiliation into `CITATION.cff`. The added reference is for cited works, not the current authors' identity.

## Reproducibility

This skill does not produce a tracked artifact beyond the `CITATION.cff` edit; emit a ReproLog only if invoked as part of a larger pipeline (see [emit-repro-log](../emit-repro-log/SKILL.md)).
