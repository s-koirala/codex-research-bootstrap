#!/usr/bin/env python3
"""PreToolUse (Write|Edit|MultiEdit|NotebookEdit) hook: flag potential PHI
(Protected Health Information) writes per HIPAA Safe Harbor section
164.514(b)(2)(i).

Cwd-scoped: only fires when the project path matches the bootstrap's
population-health globs (epidemiolog*, population-health*, clinical*,
cohort*). On non-matching cwd, returns no decision (no-op).

Detection is conservative - high-confidence syntactic patterns only. Subtle
PHI (free-text clinical notes containing implicit identifiers) cannot be
detected reliably by regex; the contributor is responsible for the broader
review.

Emits `permissionDecision: ask` (not deny) so the contributor can override
with a one-word rationale. Fails open on any exception - never blocks a write
on hook error. Python 3.10+ stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Population-health cwd globs (case-insensitive prefix-on-segment match).
# Generalized from the bootstrap's epi-cwd glob list (see AGENTS.md
# "Methodology mandates / Epi cwds"). Each entry is a prefix that any path
# segment must start with; no required infix beyond the prefix itself.
_EPI_PREFIX_SEGMENTS = (
    "epidemiolog",        # epidemiolog*
    "population-health",  # population-health*
    "clinical",           # clinical*
    "cohort",             # cohort*
)

# Excluded path segments - don't fire on synthetic fixture/test data.
_EXCLUDED_SEGMENTS = {"tests", "test", "fixtures", "fixture", "examples"}

# HIPAA Safe Harbor 18 identifiers - regex patterns for syntactic detection.
# Each tuple: (label, regex, description).
_PHI_PATTERNS = [
    # (1) SSN: NNN-NN-NNNN (and 9-digit no-hyphen with context)
    ("SSN",
     re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
     "Social Security Number pattern (XXX-XX-XXXX)"),
    # (4-5) Phone: various US formats
    ("PHONE",
     re.compile(r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
     "Phone number pattern"),
    # (6) Email
    ("EMAIL",
     re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "Email address"),
    # (3) Dates: full DOB-like patterns (with day, not just year)
    ("DATE_FULL",
     re.compile(r"\b(0[1-9]|1[0-2])[/\-.](0[1-9]|[12]\d|3[01])[/\-.](19|20)\d{2}\b"),
     "Full date (MM/DD/YYYY) - Safe Harbor allows year only"),
    # (2) ZIP > 3 digits
    ("ZIP",
     re.compile(r"\b\d{5}(?:-\d{4})?\b"),
     "5-digit ZIP code - Safe Harbor allows first 3 digits only"),
    # (15) IPv4
    ("IPV4",
     re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})\b"),
     "IPv4 address"),
    # (8) MRN-like (common formats: MRN12345678, MR-XXXX-XXXX)
    ("MRN",
     re.compile(r"\b(?:MRN|MR)[-_:#\s]*[A-Z]?\d{6,12}\b", re.I),
     "Medical Record Number pattern"),
]

# Tokens that indicate the line is itself a regex/pattern definition, not
# real data (avoid false-positive cycle on this hook scanning itself).
_SELF_REFERENCE_TOKENS = ("pre_write_phi_guard", "PHI_PATTERNS", "re.compile",
                          "regex", "Safe Harbor", "<<", "# fixture")


def _project_dir() -> Path:
    """Prefer CODEX_PROJECT_DIR; fall back to CLAUDE_PROJECT_DIR; then cwd."""
    for env_var in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        v = os.environ.get(env_var)
        if v:
            return Path(v).resolve()
    return Path(os.getcwd()).resolve()


def cwd_is_epi(cwd: Path) -> bool:
    """True iff some path segment starts with one of the epi-prefix
    fragments. Case-insensitive for cross-platform safety."""
    for seg in (p.lower() for p in cwd.parts):
        for prefix in _EPI_PREFIX_SEGMENTS:
            if seg.startswith(prefix):
                return True
    return False


def is_excluded_path(path_str: str) -> bool:
    """True if any path segment is in _EXCLUDED_SEGMENTS or path name matches."""
    parts = {seg.lower() for seg in Path(path_str).parts}
    if _EXCLUDED_SEGMENTS & parts:
        return True
    name = Path(path_str).name.lower()
    if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
        return True
    return False


def is_self_reference(text: str) -> bool:
    """True if text appears to be regex definitions / hook code, not data."""
    return any(tok in text for tok in _SELF_REFERENCE_TOKENS)


def scan_for_phi(text: str) -> list[tuple[str, str, int]]:
    """Return list of (label, snippet, line_no) for PHI matches.

    Skips lines that look like regex definitions / hook code (self-reference).
    """
    matches: list[tuple[str, str, int]] = []
    if is_self_reference(text):
        return matches  # don't scan our own source code
    for line_no, line in enumerate(text.splitlines(), start=1):
        if is_self_reference(line):
            continue
        for label, pattern, _desc in _PHI_PATTERNS:
            for m in pattern.finditer(line):
                snippet = m.group(0)
                if len(snippet) > 40:
                    snippet = snippet[:40] + "..."
                matches.append((label, snippet, line_no))
                if len(matches) >= 5:  # justify: cap reported issues at 5 to keep prompt scannable
                    return matches
    return matches


def extract_new_content(tool_input: dict) -> str:
    """Concatenate all write-content fields (mirror of pre_write_seed_guard pattern)."""
    parts: list[str] = []
    if "content" in tool_input:
        parts.append(str(tool_input["content"]))
    if "new_string" in tool_input:
        parts.append(str(tool_input["new_string"]))
    edits = tool_input.get("edits", [])
    if isinstance(edits, list):
        for e in edits:
            if isinstance(e, dict) and "new_string" in e:
                parts.append(str(e["new_string"]))
    nb_source = tool_input.get("new_source")
    if nb_source:
        parts.append(str(nb_source))
    return "\n".join(parts)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open
    tool_input = payload.get("tool_input", {})

    raw_path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not raw_path:
        return 0

    # Cwd check: must be in a population-health project
    cwd = _project_dir()
    if not cwd_is_epi(cwd):
        return 0  # no-op outside epi cwd

    # Path-exclusion check
    if is_excluded_path(raw_path):
        return 0

    new_text = extract_new_content(tool_input)
    if not new_text.strip():
        return 0

    matches = scan_for_phi(new_text)
    if not matches:
        return 0

    # Build the ask reason
    issues_str = "; ".join(f"L{ln}: {label} '{snip}'" for label, snip, ln in matches)
    reason = (
        f"Potential HIPAA Safe Harbor PHI detected in write to {Path(raw_path).name}: "
        f"{issues_str}. "
        f"Per the bootstrap's population-health mandates (see AGENTS.md 'Epi cwds'), "
        f"PHI must not leave the project's data/ directory. If this is synthetic / "
        f"de-identified data, proceed with a brief justification (e.g., 'fixture data', "
        f"'pre-redacted sample'). Otherwise, redact before writing. Reference: HHS "
        f"HIPAA Safe Harbor section 164.514(b)(2)."
    )
    if len(reason) > 1000:  # justify: keep ask-prompt scannable; truncate at 1000 chars
        reason = reason[:999] + "..."

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Fail-open on any exception; never block a write on hook error.
        sys.exit(0)
