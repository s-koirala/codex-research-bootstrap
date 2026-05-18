#!/usr/bin/env python3
"""Bootstrap a new project working directory with the research-project canonical layout.

Phase: directory tree + .gitkeep files + manifest.json + git init + template
rendering (.tmpl files under `tools/bootstrap_templates/`).

Reproducibility: the bootstrap script itself is a reproducible artifact. We
record into the project's `manifest.json`:
  - bootstrap_script_version (SemVer 2.0.0)
  - bootstrap_script_git_head (git SHA of the bootstrap repo at bootstrap time)
  - python_version pin (resolved from the bootstrap repo's pyproject.toml,
    or from a local pyproject.toml if one already exists in the scaffolded
    project; cached in $CODEX_HOME/cache/bootstrap_python_version.txt for
    offline reruns)
  - per-dir SHA-256 of the directory listing (recursive; for idempotency check)
  - per-file SHA-256 of every templated file
  - rules_file: which rules file activates for the chosen --kind (None for
    publishing/generic in the bootstrap; consumers can add a project-specific
    rule and update the manifest)
  - venv_created: bool
  - timestamp_utc

Idempotency mechanism:
  On second invocation, the script:
    1. Reads existing manifest.json.
    2. Recomputes the current per-dir SHAs.
    3. If all SHAs match AND bootstrap_script_git_head matches current
       bootstrap-repo HEAD -> exit 0 with "in sync"; no writes.
    4. If a target path is missing -> create it, update manifest.
    5. If bootstrap_script_git_head differs (template source drift) ->
       exit non-zero with a --migrate hint; never silent overwrite.

Rollback: with --rollback-on-fail, any exception after the project directory
is created triggers shutil.rmtree on the newly-created directory. Never
touches an existing tree (idempotent re-run preserves user content).

Hard constraints:
- Python 3.11+ stdlib only (no jinja2; templates use str.replace on
  `<<KEY>>` placeholders)
- All numeric thresholds documented inline with `# justify:` comments
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

# SemVer 2.0.0; bump on template or layout change.
_SCRIPT_VERSION = "0.2.0"

# Bootstrap template source dir (relative to this script; bootstrap-repo-local).
_BOOTSTRAP_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_DIR = _BOOTSTRAP_REPO_ROOT / "tools" / "bootstrap_templates"
# Shared template dir (top-level templates/ under the bootstrap repo).
_SHARED_TEMPLATE_DIR = _BOOTSTRAP_REPO_ROOT / "templates"

# Subdirs created for all --kind variants.
_BASE_SUBDIRS = (
    "src",
    "tests",
    "scripts",
    "notebooks",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/external",
    "docs/audits",
    "docs/decisions",
    "docs/literature",
    "docs/methodology",
    "docs/reports",
    "docs/research_notes",
    "docs/templates",
    "research",
    "reports",
    "artifacts/models",
    "artifacts/runs",
    # Both `artifacts/runs/` and top-level `runs/` are emitted intentionally:
    # `runs/` is a common interactive-experiment scratch dir; `artifacts/runs/`
    # is the persisted-run home. Consumers can drop one if their workflow
    # only uses the other.
    "runs",
    "config",
    "logs/reproducibility",
    # for pip_freeze_<sha>.txt files
    "logs/reproducibility/env",
    "outputs",
)

# Kind-conditional extras.
_KIND_EXTRAS = {
    "quant": (
        "config/instruments",
        "research/00_literature_review",
        "research/01_hypothesis_register",
        "logs/promotions",
    ),
    "epi": (
        "docs/protocol",
        "data/processed/_provenance",
        "logs/imputation",
    ),
    "publishing": (
        "manuscript",
        "manuscript/figures",
        "manuscript/supplement",
        "submissions",
    ),
    "generic": (),
}

# Mapping --kind -> activating rule snippet path (informational). The
# bootstrap ships quant and epi rule snippets; publishing rules are
# deliberately not shipped because the source-layer publishing policy is
# identity-bound. Consumers who need a publishing rule should author one
# locally and set the manifest's `rules_file` field accordingly.
_KIND_RULES = {
    "quant": "rules/quant-project.md",
    "epi": "rules/population-health.md",
    "publishing": None,
    "generic": None,
}

# Python-version cache. Honors $CODEX_HOME (default ~/.codex/). Falls back to
# a temp dir if neither path is writable.
_CODEX_HOME = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
_CACHE_DIR = _CODEX_HOME / "cache"
_PYTHON_VERSION_CACHE_FILENAME = "bootstrap_python_version.txt"

# Subprocess timeout for git commands. justify: git rev-parse p99 < 1s on
# warm repo; 30s margin covers cold-start + fs flush.
_SUBPROCESS_TIMEOUT_SEC = 30

# Fallback Python version pin if neither the bootstrap repo's nor the new
# project's pyproject.toml advertises one. justify: 3.11 is the floor for
# typing.Self / Exception groups, and 3.13 is the upper bound that most
# downstream scientific-Python wheels currently support; pin the same
# `>=3.11,<3.14` shape used throughout the bootstrap.
_FALLBACK_PYTHON_VERSION = ">=3.11,<3.14"


def run(cmd: list[str], cwd: Path | None = None,
        check: bool = False, capture: bool = True,
        timeout: int = _SUBPROCESS_TIMEOUT_SEC) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=capture, text=True,
        check=check, timeout=timeout,
    )


def _python_version_cache_path() -> Path | None:
    """Return the writable cache path, or None if no writable location exists."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return _CACHE_DIR / _PYTHON_VERSION_CACHE_FILENAME
    except OSError:
        try:
            tmp_cache = Path(tempfile.gettempdir()) / "codex-research-bootstrap-cache"
            tmp_cache.mkdir(parents=True, exist_ok=True)
            return tmp_cache / _PYTHON_VERSION_CACHE_FILENAME
        except OSError:
            return None


def _read_requires_python(pyproject: Path) -> str | None:
    """Parse `requires-python = "..."` from a local pyproject.toml file.

    Stdlib-only: avoids tomllib so the script works on the broadest range of
    interpreters even if a consumer pins a Python older than 3.11. A simple
    regex is sufficient: the field is always a single line in the canonical
    PEP 621 form.
    """
    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r'^\s*requires-python\s*=\s*"([^"]+)"', content, re.M)
    return m.group(1) if m else None


def resolve_python_version(target_project_root: Path | None = None) -> str:
    """Resolve the requires-python pin for the new project.

    Resolution order:
      1. A pre-existing `pyproject.toml` in the scaffolded project (consumer
         already opinionated about Python version - respect it).
      2. The bootstrap repo's own `pyproject.toml` (the bootstrap was tested
         against this version).
      3. Cached value at $CODEX_HOME/cache/bootstrap_python_version.txt
         (last-known good).
      4. Hard-coded fallback `_FALLBACK_PYTHON_VERSION`.

    The cache is invalidated by user manually removing the cache file; no
    TTL. Writes to the cache only on a fresh resolution (steps 1-2).
    """
    # Step 1: project-local pyproject.toml (if scaffolding into an existing dir).
    if target_project_root is not None:
        local_pp = target_project_root / "pyproject.toml"
        if local_pp.is_file():
            v = _read_requires_python(local_pp)
            if v:
                return v

    # Step 2: bootstrap repo pyproject.toml.
    bootstrap_pp = _BOOTSTRAP_REPO_ROOT / "pyproject.toml"
    if bootstrap_pp.is_file():
        v = _read_requires_python(bootstrap_pp)
        if v:
            cache_path = _python_version_cache_path()
            if cache_path is not None:
                try:
                    cache_path.write_text(v, encoding="utf-8")
                except OSError:
                    pass
            return v

    # Step 3: cached value.
    cache_path = _python_version_cache_path()
    if cache_path is not None and cache_path.exists():
        try:
            cached = cache_path.read_text(encoding="utf-8").strip()
            if cached:
                return cached
        except OSError:
            pass

    # Step 4: hard-coded fallback.
    return _FALLBACK_PYTHON_VERSION


def script_git_head() -> str:
    """git rev-parse HEAD for the bootstrap repo; 'unknown' on failure."""
    try:
        r = run(["git", "-C", str(_BOOTSTRAP_REPO_ROOT), "rev-parse", "HEAD"])
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "unknown"
    return r.stdout.strip() if r.returncode == 0 else "unknown"


def sha256_dir_listing(path: Path) -> str:
    """SHA-256 of the sorted POSIX-relative listing of files/dirs under `path`.

    Used for idempotency check: bootstrap-generated tree should match its
    manifest's per-dir SHA after re-run.

    Excludes:
      - `.git/` and contents (changes after `git init`; would break idempotency)
      - `.venv/` and contents (uv venv populates this with hundreds of files)
      - `__pycache__/`, `*.pyc` (Python bytecode cache)
      - `manifest.json` itself (its own SHA would chicken-and-egg)
    """
    if not path.is_dir():
        return ""
    excluded_prefixes = (".git/", ".venv/", "venv/", "__pycache__/")
    excluded_names = ("manifest.json",)
    entries = []
    for p in path.rglob("*"):
        rel = str(PurePosixPath(*p.relative_to(path).parts))
        if any(rel.startswith(pref) or f"/{pref}" in f"/{rel}/"
               for pref in excluded_prefixes):
            continue
        if p.name in excluded_names:
            continue
        if p.suffix == ".pyc":
            continue
        entries.append(f"{rel}\t{'d' if p.is_dir() else 'f'}")
    payload = "\n".join(sorted(entries)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_write_json(path: Path, payload: dict) -> Path:
    """Atomic-write idiom: sibling temp + fsync + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
    tmp = tempfile.NamedTemporaryFile(
        mode="wb", dir=str(path.parent),
        prefix=f".{path.name}.", suffix=".tmp", delete=False,
    )
    tmp_path = Path(tmp.name)
    try:
        try:
            tmp.write(data); tmp.flush(); os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return path


def build_dir_tree(project_root: Path, kind: str, dry_run: bool = False) -> list[str]:
    """Create base + kind-extra subdirs with .gitkeep sentinels. Returns the
    list of subdir paths (POSIX-relative) that exist after the call."""
    subdirs = list(_BASE_SUBDIRS) + list(_KIND_EXTRAS[kind])
    created: list[str] = []
    for sub in subdirs:
        d = project_root / sub
        if not d.exists():
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
            created.append(sub)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists() and not dry_run:
            gitkeep.touch()
    return subdirs


def render_template(
    template_path: Path,
    ctx: dict[str, str],
) -> str:
    """Substitute <<KEY>> placeholders with ctx[KEY]. Unknown placeholders
    pass through unchanged (preserves <<TODO: ...>> guidance markers in
    rendered bodies)."""
    text = template_path.read_text(encoding="utf-8")
    for key, val in ctx.items():
        text = text.replace(f"<<{key}>>", val)
    return text


def template_files_for(kind: str) -> list[tuple[str, str]]:
    """Return list of (template_name, target_relative_path) for the kind.

    Always-emitted (8 files) plus kind-specific extras (1-2 files).
    """
    always = [
        ("CLAUDE.md.tmpl", "CLAUDE.md"),
        ("README.md.tmpl", "README.md"),
        ("CHANGELOG.md.tmpl", "CHANGELOG.md"),
        ("LICENSE.tmpl", "LICENSE"),
        (".gitignore.tmpl", ".gitignore"),
        (".gitattributes.tmpl", ".gitattributes"),
        ("pyproject.toml.tmpl", "pyproject.toml"),
        (".pre-commit-config.yaml.tmpl", ".pre-commit-config.yaml"),
    ]
    if kind == "quant":
        always.append(("hypothesis_backlog.md.tmpl", "hypothesis_backlog.md"))
    elif kind == "epi":
        always.append(("protocol_v0.md.tmpl", "docs/protocol/protocol_v0.md"))
    elif kind == "publishing":
        always.append(("manuscript.md.tmpl", "manuscript/manuscript.md"))
        always.append(("ai_assistance_statement.md.tmpl", "docs/ai_assistance_statement.md"))
    return always


def render_all_templates(
    project_root: Path,
    kind: str,
    name: str,
    python_version: str,
    user_email: str | None,
    description: str = "",
) -> dict[str, str]:
    """Render every template; write to target path; return {target: sha256}.

    Skips files that already exist (preserves user edits across re-runs).
    Returns the SHA-256 map for the manifest's `files` field.
    """
    head = script_git_head()
    date = dt.date.today().isoformat()
    year = str(dt.date.today().year)
    rules_file = _KIND_RULES[kind] or "(none - generic or publishing kind; consumer-supplied)"
    # justify: MIT is the default for new research-tooling projects; align
    # with the bootstrap repo's own LICENSE.
    license_id = "MIT"
    author = user_email.split("@")[0] if user_email else "<<TODO: author>>"

    scope_text = {
        "quant": "Quant research project. Hypothesis-driven; pre-registered design.md per hypothesis; "
                 "walk-forward backtest with purge + embargo; Hansen SPA gate over the strategy family.",
        "epi": "Population-health research project. STROBE/CONSORT/STARD/TRIPOD reporting per study "
               "design; DAG-driven adjustment-set selection; E-value sensitivity per primary causal estimate.",
        "publishing": "Manuscript or publication artifact. ICMJE-compliant AI-assistance disclosure required. "
                      "Identity hygiene enforced via tools/check_identity.py.",
        "generic": "Generic research/scratch project. No kind-specific rules activate; project-level "
                   "AGENTS.md (per-subdirectory) still applies.",
    }[kind]

    # justify: STROBE is the default reporting standard for epi projects;
    # consumers override via docs/protocol/protocol_v0.md.
    reporting_standard = {
        "epi": "STROBE",
    }.get(kind, "")

    # BOOTSTRAP_ROOT: install location of the bootstrap repo's tools and
    # hooks. DOTFILES is kept as an alias for backward compatibility with
    # templates still using the legacy placeholder name.
    bootstrap_root_value = str(_CODEX_HOME).replace("\\", "/")

    ctx = {
        "NAME": name,
        "DESCRIPTION": description or f"{name} ({kind} project bootstrapped from codex-research-bootstrap)",
        "KIND": kind,
        "DATE": date,
        "YEAR": year,
        "RULES_FILE": rules_file,
        "PYTHON_VERSION": python_version,
        "BOOTSTRAP_SCRIPT_HEAD": head[:12] if head != "unknown" else "unknown",
        "LICENSE": license_id,
        "AUTHOR": author,
        "SCOPE_DESCRIPTION": scope_text,
        "REPORTING_STANDARD": reporting_standard,
        "BOOTSTRAP_ROOT": bootstrap_root_value,
        # Alias for legacy <<DOTFILES>> placeholders in pre-port templates.
        "DOTFILES": bootstrap_root_value,
        "HYPOTHESIS_ROWS": "| H001 | 1 | <<TODO>> | designed | <<DOI>> | seed hypothesis |",
        "MODEL_ID": "<<TODO: model identifier (e.g., claude-opus-4-7 or gpt-5)>>",
        "MODEL_VERSION": "<<TODO: model identifier>>",
        "ROLE": "<<TODO: idea | code | prose | audit | multi>>",
    }

    file_shas: dict[str, str] = {}
    for tmpl_name, target_rel in template_files_for(kind):
        # Resolve template source: bootstrap_templates/ first; fall back to
        # the shared templates/ tree (where the .tmpl name without the suffix
        # is the canonical filename, e.g. `CITATION.cff.tmpl` lives under
        # templates/ not tools/bootstrap_templates/).
        src = _TEMPLATE_DIR / tmpl_name
        if not src.exists():
            src = _SHARED_TEMPLATE_DIR / tmpl_name.removesuffix(".tmpl")
        if not src.exists():
            print(f"WARN: template not found: {tmpl_name}", file=sys.stderr)
            continue

        target = project_root / target_rel
        if target.exists():
            # Preserve user edits; record current SHA but do not overwrite.
            file_shas[target_rel] = hashlib.sha256(target.read_bytes()).hexdigest()
            continue

        rendered = render_template(src, ctx)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        file_shas[target_rel] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    # Also emit CITATION.cff from the shared template.
    cff_src = _SHARED_TEMPLATE_DIR / "CITATION.cff.tmpl"
    cff_target = project_root / "CITATION.cff"
    if cff_src.exists() and not cff_target.exists():
        rendered = render_template(cff_src, {
            **ctx,
            "TITLE": name,
            "TYPE": "software",
            "ABSTRACT": ctx["DESCRIPTION"],
            "VERSION": "0.0.1",
            "URL": f"https://github.com/<your-org>/{name}",
            "REPO_URL": f"https://github.com/<your-org>/{name}",
            "LICENSE_SPDX": license_id,
            "KEYWORD1": kind,
            "KEYWORD2": "research",
            "DOI": "<<TODO: Zenodo concept DOI on first release>>",
            "ORCID": "<<TODO: ORCID or omit>>",
            "CITE_TYPE": "article",
            "CITE_TITLE": "<<TODO>>",
            "CITE_YEAR": year,
            "CITE_JOURNAL": "<<TODO>>",
            "CITE_DOI": "<<TODO>>",
        })
        cff_target.write_text(rendered, encoding="utf-8")
        file_shas["CITATION.cff"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    return file_shas


def build_manifest(
    project_root: Path,
    kind: str,
    python_version: str,
    venv_created: bool,
    subdirs: list[str],
    file_shas: dict[str, str] | None = None,
) -> dict:
    """Compose the manifest.json payload."""
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    head = script_git_head()
    return {
        "bootstrap_script_version": _SCRIPT_VERSION,
        "bootstrap_script_git_head": head,
        "kind": kind,
        "rules_file": _KIND_RULES[kind],
        "python_version": python_version,
        "venv_created": venv_created,
        "timestamp_utc": now,
        "subdirs": sorted(subdirs),
        "subdir_listing_sha256": sha256_dir_listing(project_root),
        "files": file_shas or {},
    }


def idempotency_check(project_root: Path, expected_kind: str) -> tuple[str, str]:
    """Compare current state to existing manifest. Returns (status, detail).

    Status one of:
      - 'in-sync'      : everything matches; no writes needed
      - 'missing-paths': some subdirs/files don't exist; will be created
      - 'script-drift' : bootstrap_script_git_head differs; bail with --migrate hint
      - 'fresh'        : no manifest; this is a first bootstrap
    """
    mp = project_root / "manifest.json"
    if not mp.exists():
        return "fresh", ""
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return "fresh", f"existing manifest unreadable: {e}"

    if m.get("kind") != expected_kind:
        return "script-drift", (
            f"manifest kind '{m.get('kind')}' != requested '{expected_kind}'. "
            "Refusing to mutate."
        )

    expected_head = script_git_head()
    if m.get("bootstrap_script_git_head") not in (expected_head, "unknown") \
            and expected_head != "unknown":
        return "script-drift", (
            f"bootstrap_script_git_head changed: manifest "
            f"{m.get('bootstrap_script_git_head','?')[:12]} != current "
            f"{expected_head[:12]}. Run with --migrate (not yet implemented) "
            "or remove manifest.json to force re-bootstrap."
        )

    current_sha = sha256_dir_listing(project_root)
    if m.get("subdir_listing_sha256") != current_sha:
        return "missing-paths", "subdir listing has drifted (paths added or removed)"

    return "in-sync", ""


def maybe_run_uv_venv(project_root: Path, python_version: str) -> bool:
    """Create .venv via `uv venv` if uv is on PATH. Returns True on success."""
    if run(["uv", "--version"]).returncode != 0:
        print("WARN: uv not on PATH; skipping venv creation. "
              "Run `uv venv && uv sync` manually after bootstrap.", file=sys.stderr)
        return False
    # uv venv accepts "3.11" or ">=3.11,<3.14" depending on version.
    py_arg = python_version.split(",")[0].lstrip(">=<! ")
    if not py_arg:
        # justify: 3.11 is the floor for typing.Self / Exception groups;
        # safe default for any project using the bootstrap.
        py_arg = "3.11"
    # justify: 60s covers cold-start interpreter download + venv create on
    # a typical broadband connection; well under the default subprocess
    # timeout used elsewhere in this script.
    r = run(["uv", "venv", "--python", py_arg], cwd=project_root, timeout=60)
    if r.returncode != 0:
        print(f"WARN: uv venv failed (returncode {r.returncode}); "
              f"stderr: {r.stderr.strip()}", file=sys.stderr)
        return False
    return True


def git_init_and_commit(project_root: Path, kind: str, script_head: str,
                        user_email: str | None = None) -> str:
    """git init + initial Conventional Commits commit. Returns a status string.

    Returns one of:
      - 'committed'        : initial commit landed
      - 'already-initialized': .git/ already exists; commit skipped
      - 'no-identity'      : user.email/user.name unset; commit skipped with
                             instructions printed
      - 'commit-failed'    : git commit returned non-zero for another reason
    """
    if (project_root / ".git").exists():
        return "already-initialized"
    run(["git", "init", "-b", "main"], cwd=project_root, check=False)
    if user_email:
        run(["git", "config", "--local", "user.email", user_email],
            cwd=project_root)
        # If user_email provided, also set user.name to match.
        run(["git", "config", "--local", "user.name",
             user_email.split("@")[0]], cwd=project_root)

    # Identity check: a commit will fail without user.email + user.name.
    email_r = run(["git", "-C", str(project_root), "config", "user.email"])
    name_r = run(["git", "-C", str(project_root), "config", "user.name"])
    if email_r.returncode != 0 or not email_r.stdout.strip() \
            or name_r.returncode != 0 or not name_r.stdout.strip():
        print("WARN: git user.email / user.name not configured. Initial commit "
              "skipped.", file=sys.stderr)
        print(f"  Configure with:", file=sys.stderr)
        print(f"    git -C {project_root} config --local user.email <your-email>",
              file=sys.stderr)
        print(f"    git -C {project_root} config --local user.name '<Your Name>'",
              file=sys.stderr)
        print(f"  Then run:", file=sys.stderr)
        print(f"    git -C {project_root} add . && git -C {project_root} commit "
              f"-m 'chore: bootstrap {project_root.name} ({kind})'",
              file=sys.stderr)
        return "no-identity"

    run(["git", "add", "."], cwd=project_root)
    msg = (f"chore: bootstrap {project_root.name} ({kind}) "
           f"--- bootstrap-script {script_head[:12]}")
    r = run(["git", "commit", "-m", msg], cwd=project_root)
    return "committed" if r.returncode == 0 else "commit-failed"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("name", help="Project name (becomes the directory name "
                                "if --path not given)")
    p.add_argument("--kind", choices=sorted(_KIND_EXTRAS.keys()), required=True,
                   help="Project kind; selects extra subdirs and informs rule activation")
    p.add_argument("--path", type=Path, default=None,
                   help="Parent directory (default: cwd); project created at <path>/<name>")
    p.add_argument("--python-version", default=None,
                   help="Python version pin (overrides pyproject.toml lookup)")
    p.add_argument("--venv", action="store_true",
                   help="Run `uv venv` after dir tree creation")
    p.add_argument("--user-email", default=None,
                   help="Set local git config user.email in the new repo")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be created; no writes")
    p.add_argument("--rollback-on-fail", action="store_true",
                   help="shutil.rmtree the newly-created dir on any exception "
                        "(only if newly-created in THIS invocation)")
    args = p.parse_args(argv)

    parent = (args.path or Path.cwd()).resolve()
    project_root = (parent / args.name).resolve()

    python_version = args.python_version or resolve_python_version(
        target_project_root=project_root if project_root.exists() else None
    )
    script_head = script_git_head()
    newly_created = not project_root.exists()

    # Idempotency check.
    if project_root.exists():
        status, detail = idempotency_check(project_root, args.kind)
        if status == "in-sync":
            print(f"in-sync: {project_root} matches manifest; no writes.")
            return 0
        if status == "script-drift":
            print(f"ERROR: {detail}", file=sys.stderr)
            return 3
        # status in ('missing-paths', 'fresh') -> proceed to (re)build.

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"project_root: {project_root}")
        print(f"kind: {args.kind}")
        print(f"python_version: {python_version}")
        print(f"bootstrap_script_git_head: {script_head[:12]}")
        print(f"newly_created: {newly_created}")
        all_subs = list(_BASE_SUBDIRS) + list(_KIND_EXTRAS[args.kind])
        print(f"subdirs ({len(all_subs)}):")
        for s in all_subs:
            print(f"  {s}/")
        return 0

    # Build.
    project_root.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}
    try:
        subdirs = build_dir_tree(project_root, args.kind, dry_run=False)
        venv_created = False
        if args.venv:
            venv_created = maybe_run_uv_venv(project_root, python_version)

        file_shas = render_all_templates(
            project_root=project_root,
            kind=args.kind,
            name=args.name,
            python_version=python_version,
            user_email=args.user_email,
        )

        manifest = build_manifest(
            project_root=project_root,
            kind=args.kind,
            python_version=python_version,
            venv_created=venv_created,
            subdirs=subdirs,
            file_shas=file_shas,
        )
        atomic_write_json(project_root / "manifest.json", manifest)

        commit_status = git_init_and_commit(
            project_root, args.kind, script_head,
            user_email=args.user_email,
        )

    except Exception as e:
        if args.rollback_on_fail and newly_created:
            print(f"ERROR during bootstrap: {e}", file=sys.stderr)
            print(f"  Rolling back: removing {project_root}", file=sys.stderr)
            shutil.rmtree(project_root, ignore_errors=True)
        else:
            print(f"ERROR during bootstrap (NO rollback; tree left at "
                  f"{project_root}): {e}", file=sys.stderr)
        return 4

    print(f"Bootstrap OK: {project_root}")
    print(f"  kind={args.kind}, python={python_version}, "
          f"venv={'created' if venv_created else 'skipped'}, "
          f"commit={commit_status}")
    print(f"  manifest: {project_root}/manifest.json "
          f"({len(manifest.get('files', {}))} tracked file(s))")
    print(f"  bootstrap_script_git_head: {script_head[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
