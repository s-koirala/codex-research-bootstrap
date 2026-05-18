"""Shared helpers for hook scripts. Keep stdlib-only."""
from __future__ import annotations


def sanitize_session_id(session_id: str | None) -> str:
    """Canonical filename-safe session id used by stop_audit_aggregator (writer)
    and session_start_provenance (aggregator-reader). MUST stay in sync.
    Alphanumeric + '-_' only, capped at 64 chars; empty/None -> 'unknown'."""
    if not session_id:
        return "unknown"
    cleaned = "".join(c for c in session_id if c.isalnum() or c in "-_")[:64]
    return cleaned or "unknown"
