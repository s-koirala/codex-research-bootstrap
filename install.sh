#!/usr/bin/env bash
# Thin POSIX wrapper for tools/install.py. Locates Python >= 3.10 and execs
# the installer with all passed arguments forwarded.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="${SCRIPT_DIR}/tools/install.py"

if [ ! -f "${INSTALLER}" ]; then
  echo "install.sh: cannot find ${INSTALLER}" >&2
  exit 2
fi

# Probe candidate interpreters; require >= 3.10.
PYTHON=""
for candidate in python3 python; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    if "${candidate}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      PYTHON="${candidate}"
      break
    fi
  fi
done

if [ -z "${PYTHON}" ]; then
  echo "install.sh: no Python >= 3.10 found on PATH (tried: python3, python)" >&2
  echo "  Install Python 3.10+ and re-run." >&2
  exit 1
fi

exec "${PYTHON}" "${INSTALLER}" "$@"
