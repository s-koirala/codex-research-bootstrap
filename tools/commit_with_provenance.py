#!/usr/bin/env python3
"""Commit staged changes with Conventional-Commits subject + provenance trailers.

Per the reproducibility mandate, every commit emits a ReproLog (13 core
fields + the `runtime` sub-object) and references it via `Repro-Log-Path:`
and `Repro-Log-SHA256:` trailers (content-addressed; tamper-detectable).

CLI:
  commit_with_provenance.py "<subject>" --role={idea|code|prose|audit|multi} \\
      [--scope-strict] [--no-repro <justification>] [--dry-run]

Behavior:
1. Verify staged changes exist; reject empty commits.
2. Recompute pip freeze inline. The bootstrap's SessionStart provenance
   cache stores only a 12-hex truncated digest; that cache cannot be the
   source of truth for the 64-hex SHA-256 the ReproLog schema requires.
   Write the freeze text to `logs/reproducibility/env/<sha256>.txt`.
3. Read `data/_manifest.json` for dataset_checksums; null if absent.
4. Emit ReproLog at `logs/reproducibility/repro_log_{run_id}.json`.
5. Compose Conventional Commits 1.0.0 subject + body trailers:
     Repro-Log-Path: <relative path>
     Repro-Log-SHA256: <64-hex of the log content>
     AI-Assistance: <model-id> (role=<--role>)
6. `git commit -F <message-file>` with the composed message.

Fail-hard conditions:
- No staged changes -> exit 1.
- Subject does not match Conventional Commits regex -> exit 1.
- No project venv detected AND --no-repro not set -> exit 2 with a
  `uv venv && uv sync` hint.
- --role missing in a publishing-cwd (cwd whose path segments contain a
  publishing-shape substring such as "publication", "manuscript",
  "preprint", or "release"; see _PUBLISHING_SUBSTRING) -> exit 1.

Inline pip-freeze rationale: the SessionStart provenance cache stores only
`{"sha": <12-hex>, "n": <count>}` for transcript brevity; reconstructing
the full 64-hex requires recomputation. Inline recompute keeps the
ReproLog the single source of truth and avoids cache/log divergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# The emit_repro_log module ships in the bootstrap repo's skills tree. We
# load it via importlib at call-time (see _load_emit_repro_log()) instead of
# inserting into sys.path at module load — module-load-time path mutation
# pollutes the import system for any caller that imports this script.
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Conventional Commits 1.0.0 subject regex.
# https://www.conventionalcommits.org/en/v1.0.0/
_CC_SUBJECT_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([\w\-./]+\))?!?: .+$"
)

# Publishing-cwd detection. Path segments whose lowercase form contains any
# of these substrings activate the --role requirement. Substring rather than
# exact-match: a manuscript repo named `myproject-manuscript` or
# `2026-preprint-foo` should activate the rule without per-user
# configuration. Bootstrap consumers can extend this list by editing the
# constant or wrapping the script.
#
# Rationale for each token:
# - "manuscript" / "publication" / "preprint" : direct publishing artifacts.
# - "release"                                 : versioned release tags / artifact directories.
# - "submission" / "submissions"              : journal-submission staging dirs (matched by "submission").
_PUBLISHING_SUBSTRING: tuple[str, ...] = (
    "publication",
    "manuscript",
    "preprint",
    "release",
    "submission",
)

_ROLE_ENUM = {"idea", "code", "prose", "audit", "multi"}

# Default AI-assistance model identifier for the trailer. Override via
# CODEX_AI_MODEL_ID env var if a project uses a different model. The string
# itself is informational (ICMJE 2026 disclosure); update on model upgrade.
_DEFAULT_MODEL_ID = os.environ.get("CODEX_AI_MODEL_ID", "<model-id>")


def _load_emit_repro_log():
    """Load the emit_repro_log module from the bootstrap repo's skills tree.

    Uses importlib.util.spec_from_file_location so the module is registered
    under a stable internal name without mutating sys.path at module-load
    time. The internal name `_emit_repro_log_bootstrap` is namespaced to
    avoid colliding with any project-local emit_repro_log module.
    """
    import importlib.util
    src = _REPO_ROOT / "skills" / "emit-repro-log" / "assets" / "emit_repro_log.py"
    spec = importlib.util.spec_from_file_location("_emit_repro_log_bootstrap", src)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {src}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(cmd: list[str], cwd: Path | None = None, check: bool = False,
        capture: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=capture, text=True,
        check=check, timeout=timeout,
    )


def find_project_python(root: Path) -> Path | None:
    """Locate the project venv interpreter via standard layouts."""
    import platform
    if platform.system() == "Windows":
        cands = [root / ".venv" / "Scripts" / "python.exe",
                 root / "venv" / "Scripts" / "python.exe"]
    else:
        cands = [root / ".venv" / "bin" / "python",
                 root / "venv" / "bin" / "python"]
    for p in cands:
        if p.exists():
            return p
    return None


def staged_changes_exist(root: Path) -> bool:
    r = run(["git", "-C", str(root), "diff", "--cached", "--quiet"])
    # exit 1 = staged changes; exit 0 = no staged changes
    return r.returncode != 0


def cwd_is_publishing(cwd: Path) -> bool:
    """True if any path segment of cwd contains a publishing-shape substring.

    Substring (rather than exact-segment) match: a directory named
    `myproject-manuscript` or `2026-preprint-foo` activates the publishing
    rule without per-user configuration. See `_PUBLISHING_SUBSTRING` for
    the active token list.
    """
    parts = [p.lower() for p in cwd.parts]
    for seg in parts:
        for token in _PUBLISHING_SUBSTRING:
            if token in seg:
                return True
    return False


def venv_available(root: Path) -> bool:
    """True if a project venv interpreter exists OR uv.lock + uv are available.

    Used as a precheck before calling repro.capture(), which itself handles the
    raw-bytes pip-freeze emission. We do not freeze here; that would duplicate
    work and risk encoding divergence (subprocess text=True does locale decode;
    re-encoding to UTF-8 can yield different bytes than the raw stdout).
    """
    if find_project_python(root) is not None:
        return True
    if (root / "uv.lock").exists():
        # `uv pip freeze` would be invoked; rely on uv being on PATH.
        return run(["uv", "--version"]).returncode == 0
    return False


def read_data_manifest(root: Path) -> dict[str, str]:
    """Read data/_manifest.json and extract per-file SHA-256 map."""
    m_path = root / "data" / "_manifest.json"
    if not m_path.exists():
        return {}
    try:
        d = json.loads(m_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    files = d.get("files", {})
    return {p: e.get("sha256", "") for p, e in files.items() if e.get("sha256")}


def staged_paths(root: Path) -> set[str]:
    r = run(["git", "-C", str(root), "diff", "--cached", "--name-only"])
    return {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}


def scope_check(root: Path) -> bool:
    """Returns True if any staged file is under artifacts/, logs/, or research/."""
    paths = staged_paths(root)
    return any(p.startswith(("artifacts/", "logs/", "research/")) for p in paths)


def discover_project_root() -> Path:
    """$CODEX_PROJECT_DIR > $CLAUDE_PROJECT_DIR > cwd."""
    for env_var in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        v = os.environ.get(env_var)
        if v:
            return Path(v).resolve()
    return Path(os.getcwd()).resolve()


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("subject", help="Conventional Commits 1.0.0 subject line")
    p.add_argument("--role", choices=sorted(_ROLE_ENUM), default=None,
                   help="AI-assistance role per ICMJE 2026; required in publishing-cwd")
    p.add_argument("--scope-strict", action="store_true",
                   help="Require staged changes to touch artifacts/, logs/, or research/")
    p.add_argument("--no-repro", default=None, metavar="JUSTIFICATION",
                   help="Skip ReproLog emission; record JUSTIFICATION in commit body")
    p.add_argument("--dry-run", action="store_true",
                   help="Compose message + show what would be committed; do not commit")
    p.add_argument("--root", type=Path, default=None,
                   help="Project root (default: discover via $CODEX_PROJECT_DIR / $CLAUDE_PROJECT_DIR or cwd)")
    p.add_argument("--model-id", default=_DEFAULT_MODEL_ID,
                   help="AI model identifier for the AI-Assistance trailer "
                        "(default: $CODEX_AI_MODEL_ID env var or '<model-id>')")
    args = p.parse_args(argv)

    root = (args.root or discover_project_root()).resolve()

    # Gate 1: staged changes exist.
    if not staged_changes_exist(root):
        print("ERROR: no staged changes (nothing to commit).", file=sys.stderr)
        return 1

    # Gate 2: subject matches Conventional Commits.
    if not _CC_SUBJECT_RE.match(args.subject):
        print("ERROR: subject does not match Conventional Commits 1.0.0.", file=sys.stderr)
        print(f"  Subject: {args.subject!r}", file=sys.stderr)
        print("  Expected: '<type>(<scope>)?!?: <description>'", file=sys.stderr)
        print("  Types: feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert", file=sys.stderr)
        return 1

    # Gate 3: --scope-strict (optional).
    if args.scope_strict and not scope_check(root):
        print("ERROR: --scope-strict set but no staged changes touch "
              "artifacts/, logs/, or research/.", file=sys.stderr)
        return 1

    # Gate 4: --role required in publishing-cwd.
    if cwd_is_publishing(root) and args.role is None and args.no_repro is None:
        print("ERROR: --role is required in publishing-cwd "
              f"(any path segment containing one of {_PUBLISHING_SUBSTRING}). "
              "Use --role={idea|code|prose|audit|multi}.", file=sys.stderr)
        return 1

    # Branch on --no-repro.
    body_lines: list[str] = []
    trailers: list[str] = []
    if args.no_repro is not None:
        body_lines.append(f"NO-REPRO: {args.no_repro}")
    else:
        # Gate 5: venv precheck (no freeze invocation here; emit_repro_log
        # handles the actual freeze with raw bytes - calling pip freeze here
        # would either duplicate work or risk encoding divergence between
        # subprocess(text=True) decoded output and the raw bytes pip wrote).
        if not venv_available(root):
            print("ERROR: cannot compute pip freeze (no project Python venv detected "
                  "and uv.lock + uv unavailable).", file=sys.stderr)
            print("  Either run `uv venv && uv sync` in the project root, or pass "
                  "--no-repro <justification>.", file=sys.stderr)
            return 2

        # Build ReproLog. emit_repro_log.capture() internally calls
        # _pip_freeze_bytes() with raw bytes (capture_output=True, no text=True)
        # and writes logs/reproducibility/env/<sha>.txt content-addressed.
        # Load the module on demand to avoid sys.path mutation at import time.
        repro = _load_emit_repro_log()
        repro_paths = repro.ProjectPaths.discover(root)
        repro_paths.ensure(repro_paths.logs_reproducibility_env)
        dataset_checksums = read_data_manifest(root)
        record = repro.capture(
            phase="deliver",
            # justify: commit op not bound to a hypothesis; "n/a" is the schema sentinel.
            hypothesis_id="n/a",
            # justify: commit op consumes no RNG; sentinel 0 since schema is int (not int|null).
            rng_seed=0,
            dataset_checksums=dataset_checksums,
            paths=repro_paths,
        )

        repro_path = repro_paths.logs_reproducibility / f"repro_log_{record.run_id}.json"
        record.write(repro_path)

        # Content-address the log file.
        log_sha = hashlib.sha256(repro_path.read_bytes()).hexdigest()
        log_rel = Path(*repro_path.relative_to(root).parts)

        trailers.append(f"Repro-Log-Path: {log_rel.as_posix()}")
        trailers.append(f"Repro-Log-SHA256: {log_sha}")

    # AI-Assistance trailer (always when role provided).
    if args.role is not None:
        trailers.append(f"AI-Assistance: {args.model_id} (role={args.role})")

    # Compose message.
    message_parts = [args.subject, ""]
    if body_lines:
        message_parts.extend(body_lines)
        message_parts.append("")
    if trailers:
        message_parts.extend(trailers)
    message = "\n".join(message_parts).rstrip() + "\n"

    if args.dry_run:
        print("=== DRY RUN: composed commit message ===")
        print(message)
        print("=== staged files ===")
        for p_ in sorted(staged_paths(root)):
            print(f"  {p_}")
        return 0

    # Commit.
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                      encoding="utf-8") as tf:
        tf.write(message)
        msg_file = tf.name
    try:
        r = run(["git", "-C", str(root), "commit", "-F", msg_file],
                capture=False, timeout=60)
        if r.returncode != 0:
            print(f"ERROR: git commit failed (exit {r.returncode}).", file=sys.stderr)
            return r.returncode
    finally:
        Path(msg_file).unlink(missing_ok=True)

    # Verify trailers landed.
    r = run(["git", "-C", str(root), "log", "-1", "--format=%B"])
    if trailers:
        for t in trailers:
            if t not in r.stdout:
                print(f"WARN: trailer not found in HEAD message: {t}", file=sys.stderr)

    head = run(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()
    print(f"Committed {head[:12]} with {len(trailers)} provenance trailer(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
