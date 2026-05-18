#!/usr/bin/env python3
"""Build or check `data/_manifest.json` for a project.

Walks `data/{raw,interim,processed,external}/` under the project root.
For each file, computes SHA-256, size, and a retrieval-provenance record.
Preserves user-supplied fields (`source_uri`, `license`, `snapshot_date`,
`notes`) across rebuilds.

Atomic write via NamedTemporaryFile + fsync + os.replace (same idiom as
`skills/emit-repro-log/assets/emit_repro_log.py`).

CLI:
  python tools/build_data_manifest.py            # rebuild (preserves user fields)
  python tools/build_data_manifest.py --check    # verify mode; non-zero on drift
  python tools/build_data_manifest.py --json     # print JSON to stdout instead of writing

Schema: `templates/data_manifest_schema.json` (JSON Schema 2020-12); the file
ships with the bootstrap and is the authoritative contract for the manifest
shape.

Project root discovery: $CODEX_PROJECT_DIR > $CLAUDE_PROJECT_DIR > nearest
ancestor containing pyproject.toml / uv.lock / poetry.lock / .git /
requirements.txt; falls back to cwd.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

# Data subdirs walked, in canonical order.
_DATA_SUBDIRS = ("raw", "interim", "processed", "external")
_PROJECT_MARKERS = ("pyproject.toml", "uv.lock", "poetry.lock", ".git", "requirements.txt")
_SUBPROCESS_TIMEOUT_SEC = 30
_SCRIPT_VERSION = "0.1.0"


def discover_project_root(start: Path | None = None) -> Path:
    """$CODEX_PROJECT_DIR > $CLAUDE_PROJECT_DIR > nearest project-marker ancestor > cwd."""
    for env_var in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        env_root = os.environ.get(env_var)
        if env_root:
            return Path(env_root).resolve()
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if any((parent / m).exists() for m in _PROJECT_MARKERS):
            return parent
    return cur


def file_sha256(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def git_head(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
            timeout=_SUBPROCESS_TIMEOUT_SEC,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def posix(p: Path) -> str:
    return str(PurePosixPath(*p.parts))


def walk_data(root: Path) -> list[Path]:
    """Files under data/{raw,interim,processed,external}/, sorted POSIX-relative."""
    data = root / "data"
    if not data.is_dir():
        return []
    out: list[Path] = []
    for sub in _DATA_SUBDIRS:
        d = data / sub
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if f.is_file() and not f.name.startswith(".gitkeep"):
                # Skip the manifest itself if it ends up under data/.
                if f.name == "_manifest.json" and f.parent == data:
                    continue
                out.append(f)
    return sorted(out, key=lambda p: posix(p.relative_to(root)))


def atomic_write_json(path: Path, payload: dict) -> Path:
    """Same atomic-write idiom as emit_repro_log.py."""
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


def build_manifest(
    root: Path,
    existing: dict | None = None,
    script_path: Path | None = None,
) -> dict:
    """Walk data/ and emit a manifest dict. Preserves user fields from `existing`."""
    existing_files = (existing or {}).get("files", {}) if existing else {}
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    head = git_head(root)
    if script_path and script_path.is_relative_to(root):
        retriever = posix(script_path.relative_to(root))
    elif script_path:
        retriever = str(script_path)
    else:
        retriever = "manual"

    files: dict[str, dict] = {}
    for f in walk_data(root):
        rel = posix(f.relative_to(root))
        sha = file_sha256(f)
        prev = existing_files.get(rel, {})

        # Preserve user-supplied fields if SHA hasn't changed; reset
        # retrieval_timestamp only if content changed.
        if prev.get("sha256") == sha:
            retrieval_ts = prev.get("retrieval_timestamp", now_iso)
            retrieval_script_used = prev.get("retriever_script", retriever)
            retrieval_head_used = prev.get("retriever_git_head", head)
        else:
            retrieval_ts = now_iso
            retrieval_script_used = retriever
            retrieval_head_used = head

        files[rel] = {
            "sha256": sha,
            "size_bytes": f.stat().st_size,
            "retrieval_timestamp": retrieval_ts,
            "retriever_script": retrieval_script_used,
            "retriever_git_head": retrieval_head_used,
            "source_uri": prev.get("source_uri"),
            "license": prev.get("license"),
            "snapshot_date": prev.get("snapshot_date"),
            "notes": prev.get("notes"),
        }

    return {
        "$generator": f"tools/build_data_manifest.py@{_SCRIPT_VERSION}",
        "$generated_at": now_iso,
        "$git_head": head,
        "files": files,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true",
                   help="Verify mode: re-compute SHAs and compare to existing manifest; exit 1 on drift")
    p.add_argument("--json", action="store_true",
                   help="Print manifest to stdout; do not write")
    p.add_argument("--root", type=Path, default=None,
                   help="Project root (default: discover from $CODEX_PROJECT_DIR / $CLAUDE_PROJECT_DIR or cwd ancestors)")
    args = p.parse_args(argv)

    root = (args.root or discover_project_root()).resolve()
    manifest_path = root / "data" / "_manifest.json"

    existing = None
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"WARN: existing {manifest_path} is invalid JSON: {e}", file=sys.stderr)

    fresh = build_manifest(root, existing=existing, script_path=Path(__file__))

    if args.check:
        if existing is None:
            print(f"FAIL: no existing manifest at {manifest_path}", file=sys.stderr)
            return 1
        # Compare per-file SHA + size; ignore generator timestamps.
        ex_files = existing.get("files", {})
        new_files = fresh["files"]
        drift = []
        for path in sorted(set(ex_files) | set(new_files)):
            ex = ex_files.get(path)
            nf = new_files.get(path)
            if ex is None:
                drift.append(f"  + {path} (new file, sha={nf['sha256'][:12]}...)")
            elif nf is None:
                drift.append(f"  - {path} (removed)")
            elif ex.get("sha256") != nf.get("sha256"):
                drift.append(f"  ~ {path} (sha {ex.get('sha256','?')[:12]}... -> {nf['sha256'][:12]}...)")
        if drift:
            print(f"DRIFT: {len(drift)} file(s) changed since manifest:", file=sys.stderr)
            for line in drift:
                print(line, file=sys.stderr)
            return 1
        print(f"OK: {len(new_files)} file(s); manifest matches working tree.")
        return 0

    if args.json:
        print(json.dumps(fresh, sort_keys=True, indent=2, ensure_ascii=False))
        return 0

    atomic_write_json(manifest_path, fresh)
    n_files = len(fresh["files"])
    print(f"Wrote {manifest_path} ({n_files} file(s) under data/).")
    if n_files == 0:
        print("  (data/ is empty or missing; manifest has 0 entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
