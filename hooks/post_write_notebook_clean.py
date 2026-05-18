#!/usr/bin/env python3
"""PostToolUse (Write|Edit|NotebookEdit) hook: auto-clean notebooks after edits.

Runs nbstripout + nbqa ruff on *.ipynb writes if those tools are on PATH.
Fails open - if either tool is absent or returns non-zero, the hook still
exits 0 and Codex continues. Python 3.10+ stdlib only.

Third-party dependencies (optional, detected at runtime):
  - nbstripout: strips notebook output cells.
  - nbqa: runs ruff over notebook code cells.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    ti = payload.get("tool_input") or {}
    path = str(ti.get("file_path") or ti.get("notebook_path") or "").strip()
    if not path.endswith(".ipynb"):
        return 0

    if shutil.which("nbstripout"):
        subprocess.run(["nbstripout", path], capture_output=True, timeout=20)
    if shutil.which("nbqa"):
        subprocess.run(["nbqa", "ruff", "check", "--fix", path], capture_output=True, timeout=30)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"post_write_notebook_clean: unhandled error: {e}", file=sys.stderr)
        sys.exit(0)
