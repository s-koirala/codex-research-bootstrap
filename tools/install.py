#!/usr/bin/env python3
"""Install the codex-research-bootstrap surface into a Codex CLI config dir.

Copies installable artifacts (skills/, agents/, hooks/, templates/,
hooks.json, config.toml) into the user-scope Codex configuration directory
($CODEX_HOME, default ~/.codex/) or project-scope <cwd>/.codex/.

Stdlib-only is intentional per the 2026-05-18 dependency-posture decision:
the bootstrap must run on a fresh Python install without a package manager.
Idempotent via SHA-256 content-hash skip; differing files are backed up
before overwrite; atomic temp-file-then-rename writes.

Invocation:
  python tools/install.py                        # user scope ($CODEX_HOME)
  python tools/install.py --scope project        # <cwd>/.codex/
  python tools/install.py --target /tmp/sandbox  # explicit target
  python tools/install.py --dry-run              # preview, no writes
  python tools/install.py --force                # overwrite on hash match

Exit: 0 ok / 1 pre-flight failed / 2 source unreadable / 3 target
unwritable / 4 backup failed / 5 manifest write failed / 6 existing
config refused (rerun with --force) / 7 source-target collision
(--scope project invoked from the bootstrap repo's own root).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_MANIFEST_NAME = ".bootstrap-manifest.json"
_PROBE_TIMEOUT = 5  # seconds; > p99 cold-start of any plausibly-installed CLI
_HASH_CHUNK = 65536  # 64 KiB; matches Python stdlib hashlib examples

# Source-tree noise that must not ship into the install target.
# Mirrors .gitignore for the dev-time artifacts that exist on disk but are
# never tracked (and so should not propagate to $CODEX_HOME).
_INSTALL_EXCLUDE_DIRS = frozenset({
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".ipynb_checkpoints",
})
_INSTALL_EXCLUDE_SUFFIXES = frozenset({".pyc", ".pyo"})

# (source-relative-to-repo, target-relative-to-CODEX_HOME).
# Sources that do not yet exist are tolerated (Phases B-E populate them).
_INSTALL_MAP: tuple[tuple[str, str], ...] = (
    ("skills", "skills"),
    (".codex/agents", "agents"),
    ("hooks", "hooks"),
    ("templates", "templates"),
    (".codex/hooks.json", "hooks.json"),
    (".codex/config.toml", "config.toml"),
)


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_HASH_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write(path: Path, payload: bytes, src_for_mode: Path | None = None) -> None:
    """Write payload to path via sibling temp + os.replace; copy mode from src."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        mode="wb", dir=str(path.parent),
        prefix=f".{path.name}.", suffix=".tmp", delete=False,
    )
    tmp_path = Path(tmp.name)
    try:
        try:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    if src_for_mode is not None:
        try:
            shutil.copymode(src_for_mode, path)
        except OSError:
            pass


def read_bootstrap_version() -> str:
    """Parse [project].version from pyproject.toml. Falls back to '0.0.1'."""
    if not _PYPROJECT.is_file():
        return "0.0.1"
    try:
        in_project = False
        for raw in _PYPROJECT.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                in_project = line == "[project]"
                continue
            if in_project and line.startswith("version"):
                return line.partition("=")[2].strip().strip('"').strip("'")
    except OSError:
        pass
    return "0.0.1"


def repo_git_head() -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True,
            timeout=_PROBE_TIMEOUT, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


# --- pre-flight --------------------------------------------------------------

def preflight(skip: bool) -> int:
    """Detect dependencies. Returns 0 ok/skip, 1 if required `codex` missing."""
    if skip:
        print("preflight: skipped (--no-pre-flight)")
        return 0
    print("preflight: detecting toolchain")
    pv = sys.version_info
    label = "ok" if (pv.major, pv.minor) >= (3, 10) else "WARN"
    print(f"  python:     {label}  {pv.major}.{pv.minor}.{pv.micro}")
    codex = shutil.which("codex")
    if not codex:
        print("  codex:      MISS  not on PATH; install via "
              "'npm i -g @openai/codex' or 'brew install --cask codex'",
              file=sys.stderr)
        return 1
    print(f"  codex:      ok    {codex}")
    for tool, kind, hint in (
        ("uv", "recommended", "env manager (https://docs.astral.sh/uv/)"),
        ("pandoc", "optional", "manuscript rendering"),
        ("ruff", "optional", "Python lint/format"),
        ("nbstripout", "optional", "notebook hygiene"),
    ):
        p = shutil.which(tool)
        print(f"  {tool:11s}ok    {p}" if p else f"  {tool:11s}note  {kind}; {hint}")
    return 0


# --- target resolution -------------------------------------------------------

def resolve_target(scope: str, target_arg: Path | None) -> Path:
    if target_arg is not None:
        return target_arg.expanduser().resolve()
    if scope == "project":
        return (Path.cwd() / ".codex").resolve()
    env = os.environ.get("CODEX_HOME")
    return (Path(env) if env else Path.home() / ".codex").expanduser().resolve()


def is_existing_codex_home(target: Path) -> bool:
    """Heuristic: target has user content not from this bootstrap.

    True when the directory has a config.toml or non-empty skills/ AND no
    .bootstrap-manifest.json (i.e., we did not put it there).
    """
    if not target.is_dir() or (target / _MANIFEST_NAME).is_file():
        return False
    for marker_file in ("config.toml", "hooks.json"):
        if (target / marker_file).is_file():
            return True
    for marker_dir in ("skills", "agents", "hooks"):
        d = target / marker_dir
        if d.is_dir() and any(d.iterdir()):
            return True
    return False


# --- planning + execution ----------------------------------------------------

def _is_excluded(path: Path) -> bool:
    """True if path is dev-time noise (bytecode caches, lint caches) that
    must not propagate from the bootstrap source tree to the install target."""
    if path.suffix in _INSTALL_EXCLUDE_SUFFIXES:
        return True
    return any(part in _INSTALL_EXCLUDE_DIRS for part in path.parts)


def iter_pairs(src_root: Path) -> list[tuple[Path, str]]:
    """(source_file, target_relative_path) for everything in _INSTALL_MAP.

    Sources that don't exist are skipped. Directories expand to their files.
    Dev-time noise (__pycache__, *.pyc, lint caches) is excluded.
    """
    pairs: list[tuple[Path, str]] = []
    for src_rel, dst_rel in _INSTALL_MAP:
        src = src_root / src_rel
        if not src.exists():
            continue
        if src.is_file():
            if _is_excluded(src):
                continue
            pairs.append((src, dst_rel))
            continue
        for f in sorted(src.rglob("*")):
            if f.is_file() and not _is_excluded(f):
                pairs.append((f, f"{dst_rel}/{f.relative_to(src).as_posix()}"))
    return pairs


def execute(  # noqa: PLR0913
    src_root: Path,
    target: Path,
    backup_root: Path,
    dry_run: bool,
    force: bool,
    verbose: bool,
) -> tuple[dict[str, str], int]:
    """Perform the install. Returns (per-file SHA-256 map, exit-code-or-0)."""
    pairs = iter_pairs(src_root)
    sha_map: dict[str, str] = {}
    if not pairs:
        print("no installable sources found yet (Phases B-E populate them)")
        return sha_map, 0

    for src, rel in pairs:
        dst = target / rel
        src_sha = sha256_file(src)
        if not dst.exists():
            action = "install"
        elif not force and src_sha == sha256_file(dst):
            action = "skip-identical"
        else:
            action = "backup+overwrite"

        if action == "skip-identical":
            print(f"skip-identical    {rel}" + (f"  sha={src_sha[:12]}" if verbose else ""))
            sha_map[rel] = src_sha
            continue

        if action == "backup+overwrite":
            print(f"backup+overwrite  {rel}  ->  {backup_root.name}/{rel}")
            if not dry_run:
                try:
                    bkp = backup_root / rel
                    bkp.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dst, bkp)
                except OSError as e:
                    print(f"ERROR: backup failed for {rel}: {e}", file=sys.stderr)
                    return sha_map, 4
        else:
            print(f"install           {rel}")

        if not dry_run:
            try:
                _atomic_write(dst, src.read_bytes(), src_for_mode=src)
            except OSError as e:
                print(f"ERROR: write failed for {rel}: {e}", file=sys.stderr)
                return sha_map, 3
        if verbose:
            print(f"  src.sha256 = {src_sha}")
        sha_map[rel] = src_sha
    return sha_map, 0


def write_manifest(target: Path, sha_map: dict[str, str], version: str) -> int:
    payload = {
        "schema": "codex-research-bootstrap.manifest/v1",
        "installed_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "bootstrap_version": version,
        "bootstrap_repo_git_head": repo_git_head(),
        "target": str(target),
        "files": dict(sorted(sha_map.items())),
    }
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    try:
        _atomic_write(target / _MANIFEST_NAME, text.encode("utf-8"))
    except OSError as e:
        print(f"ERROR: manifest write failed: {e}", file=sys.stderr)
        return 5
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="install.py",
        description=__doc__.splitlines()[0] if __doc__ else None,
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # --scope and --target are mutually exclusive: --target wins if both are
    # specified (the mutex group raises a clear error rather than silently
    # ignoring one).
    where = p.add_mutually_exclusive_group()
    where.add_argument("--scope", choices=("user", "project"), default="user",
                       help="user = $CODEX_HOME (default); project = <cwd>/.codex/")
    where.add_argument("--target", type=Path, help="Explicit target directory")
    p.add_argument("--dry-run", action="store_true", help="Preview; do not write")
    p.add_argument("--force", action="store_true", help="Overwrite on hash match")
    p.add_argument("--backup-dir", type=Path,
                   help="Backup dir (default: <target>/.bootstrap-backups/<ts>/)")
    p.add_argument("--no-pre-flight", action="store_true", help="Skip detection (CI)")
    p.add_argument("-v", "--verbose", action="store_true", help="SHA-256 details")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if preflight(args.no_pre_flight) != 0:
        return 1
    if not _REPO_ROOT.is_dir():
        print(f"ERROR: repo root not readable: {_REPO_ROOT}", file=sys.stderr)
        return 2

    target = resolve_target(args.scope, args.target)
    print(f"target: {target}")

    # Safety: --scope project from the bootstrap repo's own root would target
    # this repository's source `.codex/` tree (i.e., source and destination
    # collide). Refuse explicitly; the user can cd elsewhere or use --target.
    repo_codex = (_REPO_ROOT / ".codex").resolve()
    if target == repo_codex:
        print(f"\nERROR: --scope project from the bootstrap repo would target its own\n"
              f"  source tree at {repo_codex}. cd to a different project directory,\n"
              "  or pass --target <path> to install elsewhere.",
              file=sys.stderr)
        return 7

    if is_existing_codex_home(target) and not args.force:
        print(f"\nWARNING: {target} looks like an existing Codex configuration\n"
              f"  (has skills/, agents/, hooks/, config.toml, or hooks.json but no\n"
              f"  {_MANIFEST_NAME}). Refusing without --force; existing files will\n"
              "  be backed up before overwrite if you re-run with --force.",
              file=sys.stderr)
        return 6

    if args.dry_run:
        print("dry-run: no writes will occur")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (args.backup_dir or (target / ".bootstrap-backups" / ts)).resolve()

    sha_map, rc = execute(
        src_root=_REPO_ROOT, target=target, backup_root=backup_root,
        dry_run=args.dry_run, force=args.force, verbose=args.verbose,
    )
    if rc != 0:
        return rc

    if args.dry_run:
        print(f"\ndry-run complete: {len(sha_map)} file(s) would be tracked")
        return 0
    if not sha_map:
        print("nothing installed (sources will appear in Phases B-E)")
        return 0

    rc = write_manifest(target, sha_map, read_bootstrap_version())
    if rc != 0:
        return rc
    print(f"\ninstall complete: {len(sha_map)} file(s) tracked in {_MANIFEST_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
