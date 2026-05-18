#!/usr/bin/env python3
"""Pre-commit hook: validate CITATION.cff against CFF v1.2.0 minimum schema.

Reads file paths from argv (pre-commit passes staged files). For each path
ending in CITATION.cff (or .cff.tmpl):
  1. Substitute <<KEY>> placeholders with sentinel strings so the template
     itself parses as YAML (placeholders must remain visible in source).
  2. YAML parse.
  3. Check CFF v1.2.0 required keys: cff-version, message, title, authors.
  4. If `cffconvert` is available on PATH, also run `cffconvert --validate -i <path>`
     against the placeholder-substituted form.
  5. Fail (exit 1) on parse failure or missing required keys; succeed (exit 0)
     otherwise. Fails open if `cffconvert` absent but YAML is well-formed.

Reproducibility-first: hook is deterministic; no network calls; no state.

Usage in .pre-commit-config.yaml:
  - repo: local
    hooks:
      - id: citation-cff
        name: CITATION.cff validator
        entry: python hooks/precommit_citation_cff.py
        language: system
        files: ^CITATION\\.cff(\\.tmpl)?$

Third-party dependencies (optional):
  - PyYAML (required for parse; error reported if missing).
  - cffconvert (optional; auxiliary validation if on PATH).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

# CFF v1.2.0 minimum required keys per https://citation-file-format.github.io/
REQUIRED_KEYS = {"cff-version", "message", "title", "authors"}

# Placeholder pattern. <<KEY>> -> "placeholder_KEY"
PLACEHOLDER_RE = re.compile(r"<<([A-Z][A-Z0-9_]*)>>")


def substitute_placeholders(text: str) -> str:
    """Replace <<KEY>> with placeholder_KEY for YAML parsing."""
    return PLACEHOLDER_RE.sub(r"placeholder_\1", text)


def validate_cff(path: Path) -> list[str]:
    """Return list of error strings; empty list = valid."""
    errors: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"cannot read {path}: {e}"]

    substituted = substitute_placeholders(raw)

    try:
        import yaml  # PyYAML
    except ImportError:
        errors.append(
            "PyYAML not installed; cannot validate. Install with `uv pip install pyyaml`."
        )
        return errors

    try:
        data = yaml.safe_load(substituted)
    except yaml.YAMLError as e:
        return [f"YAML parse error in {path}: {e}"]

    if not isinstance(data, dict):
        return [f"{path}: top-level must be a mapping, got {type(data).__name__}"]

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"{path}: missing required keys: {sorted(missing)}")

    # cff-version must be 1.2.0 exactly (forward-compat: warn if newer)
    cff_v = data.get("cff-version")
    if cff_v and str(cff_v) != "1.2.0":
        errors.append(
            f"{path}: cff-version is '{cff_v}'; expected '1.2.0'. "
            "Update validator before bumping."
        )

    # authors must be a non-empty list
    authors = data.get("authors")
    if authors is not None and (not isinstance(authors, list) or len(authors) == 0):
        errors.append(f"{path}: authors must be a non-empty list")

    # If cffconvert is available, run it against the substituted form
    if shutil.which("cffconvert"):
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".cff", delete=False, encoding="utf-8"
        ) as tf:
            tf.write(substituted)
            tmp_path = tf.name
        try:
            r = subprocess.run(
                ["cffconvert", "--validate", "-i", tmp_path],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                errors.append(
                    f"{path}: cffconvert --validate failed: "
                    f"{r.stderr.strip() or r.stdout.strip()}"
                )
        except (subprocess.TimeoutExpired, OSError) as e:
            errors.append(f"{path}: cffconvert invocation failed: {e}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        # pre-commit always passes at least one path; bare invocation = no-op
        return 0

    all_errors: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            continue
        all_errors.extend(validate_cff(path))

    if all_errors:
        print("CITATION.cff validation FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
