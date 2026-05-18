#!/usr/bin/env python3
"""Identity-hygiene scanner. Two-tier design (this script source must be
identity-hygiene-clean, so it contains NO literal maintainer tokens):

  Tier 1 (here): SHAPE patterns - personal-email TLDs, Windows / POSIX
                 home-directory path prefixes - as regex alternations.
  Tier 2 (loaded at runtime from `tools/check_identity_tokens.local.txt`,
                 gitignored): maintainer-specific literals. One token per
                 line; `#` for comments; `# === <label> ===` for category
                 headers. Copy `check_identity_tokens.example.txt` to
                 `.local.txt` and populate. Without the local file only
                 Tier 1 runs (with a one-line note).

Invocation: `python tools/check_identity.py [--staged | path/...]`
Exit: 0 clean / 1 matches / 2 local file unreadable / 3 git failed.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LOCAL_TOKEN_FILE = _REPO_ROOT / "tools" / "check_identity_tokens.local.txt"
_EXAMPLE_TOKEN_FILE = _REPO_ROOT / "tools" / "check_identity_tokens.example.txt"

_PRUNE_DIRS = frozenset({  # keep in sync with .gitignore
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules",
    ".bootstrap-backups", "dist", "build", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".ipynb_checkpoints",
})
# The example token file would self-flag if scanned; skip it.
_SKIP_FILENAMES = frozenset({"check_identity_tokens.example.txt"})
_BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".tar",
    ".whl", ".so", ".dylib", ".dll", ".exe", ".bin", ".docx", ".xlsx",
    ".pptx", ".ico", ".woff", ".woff2", ".ttf", ".eot",
})

# Tier 1 generic patterns. Category labels (not literals) appear in output
# so reports never echo the leaked content. Patterns use regex alternation,
# not the literal forbidden strings.
_GENERIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("personal-email", re.compile(
        r"@(?:gmail|yahoo|outlook|hotmail|icloud|protonmail|aol|live|me)\."
        r"(?:com|net|org|co\.[a-z]{2}|io)", re.IGNORECASE,
    )),
    # Windows: drive + Users + name (name not an envvar/template placeholder).
    ("windows-home-path", re.compile(r"[A-Za-z]:[\\/]Users[\\/](?![<%$])[A-Za-z0-9_.-]+")),
    # POSIX: /home/<name> or /Users/<name>; lowercase first char dodges
    # generic multi-user paths like /Users/Shared, /home/Public.
    ("unix-home-path", re.compile(
        r"(?<![A-Za-z0-9_])/(?:home|Users)/(?![<%$])[a-z][A-Za-z0-9_.-]+")),
)


def _should_skip(p: Path) -> bool:
    return p.name in _SKIP_FILENAMES or p.suffix.lower() in _BINARY_SUFFIXES


def load_local_tokens() -> tuple[list[tuple[str, str]], int]:
    """Return ((category, token) pairs, status). 0 ok / 1 missing / 2 unreadable."""
    if not _LOCAL_TOKEN_FILE.is_file():
        return [], 1
    try:
        raw = _LOCAL_TOKEN_FILE.read_text(encoding="utf-8")
    except OSError:
        return [], 2
    tokens, current = [], "maintainer-token"
    section_re = re.compile(r"^\s*#\s*===\s*(.+?)\s*===\s*$")
    for s in (ln.strip() for ln in raw.splitlines()):
        if not s:
            continue
        if (m := section_re.match(s)):
            current = m.group(1).strip() or "maintainer-token"
        elif not s.startswith("#"):
            tokens.append((current, s))
    return tokens, 0


def _git_files(args: list[str], root: Path = _REPO_ROOT, timeout: int = 15) -> tuple[list[str] | None, str]:
    """Run git in `root` with `args`; return (lines, error). lines=None on failure."""
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True, check=False, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return None, str(e)
    if r.returncode != 0:
        return None, f"git rc={r.returncode}: {r.stderr.strip()}"
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()], ""


def iter_repo_files(root: Path) -> list[Path]:
    """Tracked + new (not-ignored) files via git; manual walk fallback."""
    lines, _ = _git_files(["ls-files", "--cached", "--others", "--exclude-standard"], root=root)
    if lines is not None:
        return [root / rel for rel in lines if (root / rel).is_file() and not _should_skip(Path(rel))]
    out, stack = [], [root]
    while stack:
        try:
            children = list(stack.pop().iterdir())
        except OSError:
            continue
        for c in children:
            if c.is_symlink():
                continue
            if c.is_dir():
                if c.name not in _PRUNE_DIRS:
                    stack.append(c)
            elif not _should_skip(c):
                out.append(c)
    return out


def iter_staged_files() -> tuple[list[Path], int]:
    lines, err = _git_files(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], timeout=10)
    if lines is None:
        print(f"check_identity: git failed in --staged mode: {err}", file=sys.stderr)
        return [], 3
    return [_REPO_ROOT / rel for rel in lines
            if (_REPO_ROOT / rel).is_file() and not _should_skip(Path(rel))], 0


def redacted_placeholder(match_length: int, line_length: int) -> str:
    """Privacy-preserving placeholder for stdout/CI logs.

    Never echoes any character from the matched span OR its surrounding
    context. The script's whole purpose is to flag identity-bound strings, so
    reproducing them in logs would defeat the safety invariant. Triage
    metadata (match length + line length) is sufficient for a maintainer to
    locate the leak; the file path + line + column already points to the
    exact source.
    """
    return f"<REDACTED match_len={match_length} line_len={line_length}>"


def scan_file(path: Path, local_tokens: list[tuple[str, str]],
              out: list[str], rel_root: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    rel = path.relative_to(rel_root).as_posix() if path.is_absolute() else str(path)
    for line_no, line in enumerate(text.splitlines(), start=1):
        for category, pat in _GENERIC_PATTERNS:
            for m in pat.finditer(line):
                out.append(f"{rel}:{line_no}:{m.start() + 1}:{category}:"
                           f"{redacted_placeholder(m.end() - m.start(), len(line))}")
        lower = line.lower()
        for category, token in local_tokens:
            if token and (idx := lower.find(token.lower())) >= 0:
                out.append(f"{rel}:{line_no}:{idx + 1}:{category}:"
                           f"{redacted_placeholder(len(token), len(line))}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="check_identity.py",
                                description=__doc__.splitlines()[0] if __doc__ else None)
    p.add_argument("--staged", action="store_true",
                   help="Scan only files staged in git (--cached); for pre-commit")
    p.add_argument("paths", nargs="*", type=Path,
                   help="Explicit file paths; overrides default tree walk")
    args = p.parse_args(argv)

    # argparse cannot make a positional `paths` mutually exclusive with a
    # store_true flag; check manually.
    if args.staged and args.paths:
        print("check_identity: --staged and explicit paths are mutually exclusive",
              file=sys.stderr)
        return 1

    local_tokens, status = load_local_tokens()
    if status == 2:
        print(f"check_identity: local token file unreadable: {_LOCAL_TOKEN_FILE}",
              file=sys.stderr)
        return 2
    if status == 1:
        print("check_identity: note - no local token file; running Tier 1 only. "
              f"Copy {_EXAMPLE_TOKEN_FILE.name} to {_LOCAL_TOKEN_FILE.name} "
              "(gitignored) to enable maintainer-specific token scanning.",
              file=sys.stderr)

    if args.staged:
        files, rc = iter_staged_files()
        if rc != 0:
            return rc
    elif args.paths:
        files = [p for p in args.paths if p.is_file()]
    else:
        files = iter_repo_files(_REPO_ROOT)

    findings: list[str] = []
    for f in files:
        scan_file(f, local_tokens, findings, _REPO_ROOT)
    for line in findings:
        print(line)
    if findings:
        print(f"\ncheck_identity: {len(findings)} potential leak(s) across "
              f"{len(files)} file(s). Resolve before commit.", file=sys.stderr)
        return 1
    print(f"check_identity: clean ({len(files)} file(s) scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
