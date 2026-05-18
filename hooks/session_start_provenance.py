#!/usr/bin/env python3
"""SessionStart hook: emit git/env/data provenance into additionalContext AND
aggregate closed-session turn files into docs/audits/session_trail_*.md.

Two responsibilities:

  (1) Provenance emission. Reports git HEAD/branch/dirty state, a hash of the
      project's pip freeze (cached by lockfile mtime to amortize cost), and a
      manifest hash of the project's data/ directory. Output goes into the
      Codex `additionalContext` of the SessionStart hook response, which the
      model sees as PROVENANCE | git: ... | deps-sha: ... | data/: ... .

  (2) Aggregation half of the Stop-event audit-trail pattern. Codex has no
      SessionEnd event; hooks/stop_audit_aggregator.py writes one JSON file
      per turn to logs/turn_<session_id>_<n>.json. On each SessionStart this
      script scans logs/turn_*.json, groups by session_id, treats any
      session_id != current as closed, aggregates each closed session's turn
      files into docs/audits/session_trail_<date>_<session_id>.md, and
      deletes the per-turn files. See AGENTS.md "Stop-event audit-trail
      aggregation".

Uses the project's venv interpreter (not the one running this hook) so
reported deps match what the project will actually run. Caches deps-sha
per-lockfile-mtime in $CODEX_HOME/cache/ (falls back to ~/.codex/cache/).

Fail-open — never blocks a session on hook error. Python 3.10+ stdlib only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

# Import shared sanitizer from hooks/_common.py. sys.path insertion is keyed
# off this script's own location, so the import works regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import sanitize_session_id  # noqa: E402


def _codex_home() -> Path:
    """Resolve $CODEX_HOME (Codex CLI config home); default ~/.codex/."""
    v = os.environ.get("CODEX_HOME")
    if v:
        return Path(v).expanduser()
    return Path.home() / ".codex"


CACHE_DIR = _codex_home() / "cache"
PROJECT_MARKERS = ("pyproject.toml", "requirements.txt", "uv.lock", "poetry.lock", "Pipfile.lock")

# Regex for the per-turn filename produced by stop_audit_aggregator.py.
# Format: turn_<session_id>_<index>_<ts_us>.json where session_id is
# [A-Za-z0-9_-]+, index is the 1-based turn ordinal, and ts_us is a
# YYYYMMDDTHHMMSSffffff microsecond-precision UTC timestamp (collision-free
# under concurrent Stop-call races; see stop_audit_aggregator.py module docstring).
_TURN_FILE_RE = re.compile(
    r"^turn_(?P<sid>[A-Za-z0-9_-]+)_(?P<idx>\d+)_(?P<ts>\d+T?\d*)\.json$"
)


def _project_dir() -> Path:
    """Resolve project dir; prefer CODEX_PROJECT_DIR, fall back to CLAUDE_PROJECT_DIR, then cwd."""
    for env_var in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        v = os.environ.get(env_var)
        if v:
            return Path(v)
    return Path(os.getcwd())


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def short_digest(text: str, n: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:n] if text else ""


def find_project_python(proj: Path) -> str | None:
    if platform.system() == "Windows":
        cand = [proj / ".venv" / "Scripts" / "python.exe", proj / "venv" / "Scripts" / "python.exe"]
    else:
        cand = [proj / ".venv" / "bin" / "python", proj / "venv" / "bin" / "python"]
    for p in cand:
        if p.exists():
            return str(p)
    return None


def is_python_project(proj: Path) -> bool:
    return any((proj / m).exists() for m in PROJECT_MARKERS)


def deps_sha(proj: Path) -> tuple[str, int] | None:
    """Return (sha, n_pkgs) for the project's deps. Cache keyed on lockfile mtimes
    so `uv add` / `pip install` invalidates the cache immediately."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    lock_sig_parts: list[str] = []
    for m in PROJECT_MARKERS:
        p = proj / m
        if p.exists():
            try:
                lock_sig_parts.append(f"{m}:{p.stat().st_mtime_ns}")
            except Exception:
                pass
    lock_sig = "|".join(lock_sig_parts) or "no-lock"
    key = hashlib.sha1((str(proj.resolve()) + "::" + lock_sig).encode()).hexdigest()[:16]
    cache_file = CACHE_DIR / f"deps_{key}.json"
    if cache_file.exists():
        try:
            d = json.loads(cache_file.read_text())
            return d["sha"], d["n"]
        except Exception:
            pass

    py = find_project_python(proj)
    if py:
        freeze = run([py, "-m", "pip", "freeze"], timeout=15)
    elif (proj / "uv.lock").exists() and os.environ.get("PATH"):
        freeze = run(["uv", "pip", "freeze"], cwd=proj, timeout=15)
    else:
        return None
    if not freeze:
        return None
    sha = short_digest(freeze)
    n = freeze.count("\n") + 1
    try:
        cache_file.write_text(json.dumps({"sha": sha, "n": n}))
    except Exception:
        pass
    return sha, n


def _aggregate_closed_sessions(proj: Path, current_session_id: str | None) -> None:
    """Scan logs/turn_*.json, group by session_id, aggregate any !=current into
    docs/audits/session_trail_<date>_<session_id>.md, then delete the per-turn
    files for the aggregated sessions. Fail-open; logs to stderr.

    Sanitization parity: the writer (stop_audit_aggregator.py) names files
    with `sanitize_session_id(payload.session_id)`, so the parsed `sid` from
    the filename is the sanitized form. To compare against the current
    SessionStart payload's raw `session_id`, we sanitize it through the same
    helper FIRST. Otherwise an open session whose raw id contains a non-
    [A-Za-z0-9_-] character would be misclassified as closed.

    Atomicity: the trail markdown is written via sibling-temp + os.replace
    so a crash mid-write leaves either the previous trail or the new trail,
    never a half-written one. Per-turn files are deleted ONLY after the
    rename succeeds.

    Forensic preservation: if a session has files but ALL records are
    unreadable, the per-turn files are LEFT IN PLACE with a stderr warning.
    Auto-deletion in this case would destroy forensic evidence.
    """
    logs_dir = proj / "logs"
    if not logs_dir.is_dir():
        return

    # Group turn files by session_id.
    by_sid: dict[str, list[Path]] = {}
    try:
        for p in logs_dir.iterdir():
            if not p.is_file():
                continue
            m = _TURN_FILE_RE.match(p.name)
            if not m:
                continue
            by_sid.setdefault(m.group("sid"), []).append(p)
    except OSError as e:
        print(f"session_start_provenance: cannot scan logs/: {e}", file=sys.stderr)
        return

    # Sanitize the live session_id to match the writer's filename-safe form
    # before comparing to parsed sids from filenames.
    current_safe = sanitize_session_id(current_session_id)

    audits_dir = proj / "docs" / "audits"
    for sid, files in by_sid.items():
        if current_session_id is not None and sid == current_safe:
            continue  # the current (open) session — skip
        # Sort by (turn_index, ts_us). The ts_us suffix is collision-free
        # under concurrent-Stop races; (idx, ts) is the canonical order.
        def _sort_key(fp: Path) -> tuple[int, str]:
            m = _TURN_FILE_RE.match(fp.name)
            if m is None:  # defensive; the grouping step already filtered
                return (10**9, "")
            try:
                return (int(m.group("idx")), m.group("ts"))
            except (TypeError, ValueError):
                return (10**9, m.group("ts") or "")

        files_sorted = sorted(files, key=_sort_key)
        records: list[dict] = []
        for fp in files_sorted:
            try:
                records.append(json.loads(fp.read_text(encoding="utf-8")))
            except Exception as e:
                print(f"session_start_provenance: skipping unreadable {fp.name}: {e}", file=sys.stderr)

        if not records:
            # All files unreadable. DO NOT delete — destroying forensic data
            # could mask an underlying corruption bug. Next SessionStart will
            # retry; an operator may move them to logs/turn_corrupted/ by hand.
            print(
                f"session_start_provenance: WARNING session {sid[:16]} has "
                f"{len(files_sorted)} per-turn file(s) but all are unreadable; "
                "leaving in place for forensic inspection.",
                file=sys.stderr,
            )
            continue

        # Date stamp from the first turn's timestamp, fallback to today.
        ts_first = records[0].get("timestamp_utc") or ""
        date_str = ts_first[:10] if len(ts_first) >= 10 else dt.date.today().isoformat()

        # Broaden exception class: a single corrupted session must not abort
        # the loop. OSError, UnicodeError, ValueError are the realistic
        # failure modes; catching Exception covers the long tail.
        try:
            audits_dir.mkdir(parents=True, exist_ok=True)
            trail_path = audits_dir / f"session_trail_{date_str}_{sid[:16]}.md"
            lines: list[str] = []
            lines.append(f"# Session trail {date_str} / session={sid[:16]}")
            lines.append("")
            lines.append(f"- Turns recorded: {len(records)}")
            if records:
                lines.append(f"- First turn: {records[0].get('timestamp_utc', 'unknown')}")
                lines.append(f"- Last turn: {records[-1].get('timestamp_utc', 'unknown')}")
                lines.append(f"- cwd: {records[0].get('cwd', 'unknown')}")
                lines.append(f"- model: {records[0].get('model', 'unknown')}")
            lines.append("")
            lines.append("## Per-turn records")
            lines.append("")
            for rec in records:
                lines.append(f"- turn {rec.get('turn_index', '?')} | "
                             f"{rec.get('timestamp_utc', '?')} | "
                             f"model={rec.get('model', '?')} | "
                             f"perm={rec.get('permission_mode', '?')}")
            trail_text = "\n".join(lines) + "\n"

            # Atomic write: temp + os.replace. Crash mid-write leaves either
            # the previous trail or no change; never a half-written file.
            tmp = trail_path.with_suffix(trail_path.suffix + ".tmp")
            try:
                tmp.write_text(trail_text, encoding="utf-8")
                os.replace(tmp, trail_path)
            except Exception:
                tmp.unlink(missing_ok=True)
                raise

            # Aggregation succeeded AND landed on disk — only NOW remove
            # the per-turn files.
            for fp in files_sorted:
                try:
                    fp.unlink()
                except OSError as e:
                    print(f"session_start_provenance: cleanup failed for {fp.name}: {e}",
                          file=sys.stderr)
        except Exception as e:
            print(f"session_start_provenance: aggregation write failed for {sid}: {e}",
                  file=sys.stderr)
            continue


def main() -> int:
    # Read the hook payload (for session_id; tolerate absence).
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    current_session_id = payload.get("session_id")
    if current_session_id is not None:
        current_session_id = str(current_session_id)

    proj = _project_dir()

    # (2) Aggregate closed-session turn files before emitting provenance, so a
    # crash in provenance still cleans up stale per-turn JSON.
    try:
        _aggregate_closed_sessions(proj, current_session_id)
    except Exception as e:
        print(f"session_start_provenance: aggregator error: {e}", file=sys.stderr)

    # (1) Provenance emission.
    parts: list[str] = []

    head = run(["git", "rev-parse", "HEAD"], cwd=proj)
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=proj)
    dirty = run(["git", "status", "--porcelain"], cwd=proj)
    if head:
        parts.append(f"git: {head[:12]} ({branch}){' [DIRTY]' if dirty else ''}")

    if is_python_project(proj):
        res = deps_sha(proj)
        if res:
            parts.append(f"deps-sha: {res[0]} ({res[1]} pkgs)")

    data_dir = proj / "data"
    if data_dir.is_dir():
        # Hash the full data/ listing; previous [:50] cap was a silent truncation
        # that produced misleading manifest-sha values on larger trees. Hashing
        # O(n) tiny filename+size strings is cheap (SHA-256 on a few hundred KB
        # of metadata is sub-millisecond).
        files = sorted(p for p in data_dir.rglob("*") if p.is_file())
        if files:
            h = hashlib.sha256()
            for f in files:
                try:
                    h.update(f.name.encode())
                    h.update(str(f.stat().st_size).encode())
                except Exception:
                    pass
            parts.append(f"data/: {len(files)} files, manifest-sha: {h.hexdigest()[:12]}")

    if not parts:
        return 0

    ctx = "PROVENANCE | " + " | ".join(parts)
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"session_start_provenance: unhandled error: {e}", file=sys.stderr)
        sys.exit(0)
