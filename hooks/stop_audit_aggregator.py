#!/usr/bin/env python3
"""Stop hook: append one per-turn JSON record to
logs/turn_<session_id>_<n>_<ts_us>.json.

Codex CLI has no SessionEnd event; the Stop event fires once per turn, not once
per session. This script implements the Stop-side of the per-turn-file +
next-SessionStart-aggregator pattern (see AGENTS.md "Stop-event audit-trail
aggregation"). The SessionStart-side aggregator lives in
hooks/session_start_provenance.py.

Per-turn-file scheme:
  logs/turn_<session_id>_<turn_index>_<ts_us>.json

`turn_index` is 1-based and derived by counting existing turn files for the
same `session_id`. The microsecond-UTC timestamp suffix `ts_us` makes the
filename collision-free even when two Stop calls for the same session race —
both observe the same N+1 turn_index, but each appends its own monotonically-
larger ts_us, so neither clobbers the other. Aggregator-side sort orders by
(idx, ts_us) so record order is recoverable. Atomic write (tempfile in same
directory + os.replace). Fail-open — never block Codex on hook error; emit
empty {} on stdout.

Python stdlib only. Hook input contract from Codex (JSON on stdin):
  session_id, transcript_path, cwd, hook_event_name, model, permission_mode.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

# Import shared sanitizer from hooks/_common.py. sys.path insertion is keyed
# off the script's own location, so the import works regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import sanitize_session_id  # noqa: E402


def _project_dir() -> Path:
    """Resolve the project directory; prefer CODEX_PROJECT_DIR, fall back to cwd."""
    for env_var in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        v = os.environ.get(env_var)
        if v:
            return Path(v)
    return Path(os.getcwd())


def _next_turn_index(logs_dir: Path, session_id: str) -> int:
    """1-based index = (existing turn files for this session_id) + 1."""
    if not logs_dir.is_dir():
        return 1
    prefix = f"turn_{session_id}_"
    existing = sum(1 for p in logs_dir.iterdir()
                   if p.is_file() and p.name.startswith(prefix) and p.suffix == ".json")
    return existing + 1


def _atomic_write_json(target: Path, data: dict) -> None:
    """Temp-file-then-rename atomic write. Target dir must exist."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".turn_", suffix=".json.tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main() -> int:
    # Read JSON payload from stdin per the Codex hook contract.
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    session_id = str(payload.get("session_id") or "unknown")
    # Canonical filename-safe id; reader-side aggregator uses the same helper.
    safe_session_id = sanitize_session_id(session_id)

    proj = _project_dir()
    logs_dir = proj / "logs"

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        now = dt.datetime.now(dt.timezone.utc)
        idx = _next_turn_index(logs_dir, safe_session_id)
        # justify: microsecond UTC timestamp suffix avoids the
        # concurrent-Stop-call race condition where two writers compute the
        # same N+1 and clobber each other. ts_us is monotonic within a single
        # process; concurrent processes collide only if both call
        # datetime.now() in the same microsecond, which would require sub-us
        # interleaving on a single Stop event — not observed in practice.
        ts_us = now.strftime("%Y%m%dT%H%M%S%f")  # YYYYMMDDTHHMMSS + 6-digit microsecond
        target = logs_dir / f"turn_{safe_session_id}_{idx}_{ts_us}.json"
        record = {
            "session_id": session_id,
            "turn_index": idx,
            "timestamp_utc": now.isoformat(timespec="seconds"),
            "cwd": str(proj),
            "hook_event_name": payload.get("hook_event_name", "Stop"),
            "model": payload.get("model"),
            "permission_mode": payload.get("permission_mode"),
            "transcript_path": payload.get("transcript_path"),
        }
        _atomic_write_json(target, record)
    except Exception as e:
        print(f"stop_audit_aggregator: write failed: {e}", file=sys.stderr)

    # Codex hooks expect a JSON response on stdout. Empty object signals no
    # decision / no additional context; never blocks the Stop event.
    print("{}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"stop_audit_aggregator: unhandled error: {e}", file=sys.stderr)
        # Always emit valid JSON even on failure so Codex parses it cleanly.
        print("{}")
        sys.exit(0)
