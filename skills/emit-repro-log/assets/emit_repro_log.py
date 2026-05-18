"""ReproLog emitter — self-contained, stdlib-only.

Emits a reproducibility-envelope JSON record before any run that writes to
`artifacts/` or `logs/`. See [../SKILL.md](../SKILL.md) for the field
contract and invocation rules; see [repro_log_schema.json](repro_log_schema.json)
for the JSON Schema.

Record shape:

  13 core fields:
    run_id, phase, hypothesis_id, timestamp_utc, git_head,
    pip_freeze_sha256, pip_freeze_path, dataset_checksums,
    rng_seed, model_hash, config_resolved_sha256, host, env_id.

  Plus a 4-field `runtime` sub-object (added 2026-05-18):
    python_version, platform, container_digest, os_release.

The `runtime` sub-object captures the OS / interpreter / container stack
under which the record was emitted, beyond the compact `host` triple. The
augmentation is motivated by Boettiger (2015), "An introduction to Docker
for reproducible research," ACM SIGOPS Oper. Syst. Rev. 49(1):71-79,
doi:10.1145/2723872.2723882, which argues that recreating a result
requires the OS distribution and (when applicable) container image
digest in addition to source-code + library versions.

Self-contained: no project-internal imports; inlines `file_sha256` and a
minimal `ProjectPaths` discovery (CODEX_PROJECT_DIR > CLAUDE_PROJECT_DIR
> pyproject.toml ancestor search > cwd).

CLI: `python emit_repro_log.py --selftest` exits 0 on round-trip success.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

# Subprocess timeout for `git rev-parse` / `uv pip freeze`. Tunable via env var.
_SUBPROCESS_TIMEOUT_SEC = int(os.environ.get("REPRO_SUBPROCESS_TIMEOUT_SEC", "30"))

# Project-root discovery markers, ordered by specificity.
_PROJECT_MARKERS = (
    "pyproject.toml", "uv.lock", "poetry.lock",
    "requirements.txt", "Pipfile.lock", ".git",
)


# --------------------------------------------------------------------------- #
# Inlined utilities (a minimal repro_envelope shim - intentionally self-
# contained so this single file can be vendored anywhere).
# --------------------------------------------------------------------------- #

def file_sha256(path: Path, chunk: int = 65536) -> str:
    """Stream-based SHA-256 of a file's bytes. Empty string on read failure."""
    try:
        h = hashlib.sha256()
        with Path(path).open("rb") as f:
            for block in iter(lambda: f.read(chunk), b""):
                h.update(block)
        return h.hexdigest()
    except OSError:
        return ""


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    logs_reproducibility: Path
    logs_reproducibility_env: Path

    @staticmethod
    def discover(start: Path | None = None) -> ProjectPaths:
        """Find project root via CODEX_PROJECT_DIR / CLAUDE_PROJECT_DIR or
        ancestor marker search.

        CODEX_PROJECT_DIR is checked first (Codex CLI convention);
        CLAUDE_PROJECT_DIR is preserved as a fallback so the skill works
        identically under both runtimes.
        """
        env_root = (
            os.environ.get("CODEX_PROJECT_DIR")
            or os.environ.get("CLAUDE_PROJECT_DIR")
        )
        if env_root:
            root = Path(env_root).resolve()
        else:
            cur = (start or Path.cwd()).resolve()
            root = cur
            for parent in [cur, *cur.parents]:
                if any((parent / m).exists() for m in _PROJECT_MARKERS):
                    root = parent
                    break
        return ProjectPaths(
            root=root,
            logs_reproducibility=root / "logs" / "reproducibility",
            logs_reproducibility_env=root / "logs" / "reproducibility" / "env",
        )

    def ensure(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# ReproLog dataclass
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ReproLog:
    run_id: str
    phase: str
    hypothesis_id: str
    timestamp_utc: str
    git_head: str
    pip_freeze_sha256: str
    pip_freeze_path: str
    dataset_checksums: dict[str, str]
    rng_seed: int
    model_hash: str | None
    config_resolved_sha256: str | None
    host: dict[str, str]
    env_id: str
    # Runtime-stack sub-object: python_version, platform, container_digest,
    # os_release. See module docstring + repro_log_schema.json for the
    # rationale (Boettiger 2015, doi:10.1145/2723872.2723882).
    runtime: dict[str, str | None]

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, path: Path) -> Path:
        """Atomically serialize this ReproLog to `path`.

        Pattern: NamedTemporaryFile in destination dir -> write -> flush ->
        os.fsync(fd) -> close -> os.replace. Atomic on POSIX and on Windows
        (MoveFileEx semantics per Python 3.3+ os.replace docs). Readers
        therefore never observe a partial file.

        Limit: SIGKILL strictly between write and rename may leave the
        tempfile on disk (target untouched). Accepted POSIX limit - no
        userspace pattern can defeat SIGKILL.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        data = json.dumps(
            payload, sort_keys=True, indent=2, ensure_ascii=False
        ).encode("utf-8")
        # Binary mode: Windows translates `\n` to `\r\n` in text mode, which
        # would break byte-identity SHA-256 checks. `delete=False` so we can
        # rename; `dir=path.parent` keeps the rename same-filesystem.
        tmp = tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        tmp_path = Path(tmp.name)
        try:
            try:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            finally:
                tmp.close()
            os.replace(tmp_path, path)
        except Exception:
            # Clean up orphan tempfile if write/fsync/replace fails.
            tmp_path.unlink(missing_ok=True)
            raise
        return path

    @staticmethod
    def read(path: Path) -> ReproLog:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return ReproLog(**payload)

    @staticmethod
    def verify(path: Path) -> bool:
        """Round-trip verification: read -> re-serialize -> compare bytes."""
        try:
            on_disk = Path(path).read_text(encoding="utf-8")
            payload = json.loads(on_disk)
            parsed = ReproLog(**payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False
        canonical = json.dumps(
            parsed.to_dict(), sort_keys=True, indent=2, ensure_ascii=False
        )
        return on_disk == canonical


# --------------------------------------------------------------------------- #
# Capture helpers
# --------------------------------------------------------------------------- #

def _git_head(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
            timeout=_SUBPROCESS_TIMEOUT_SEC,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def _pip_freeze_bytes() -> bytes:
    """Prefer `uv pip freeze` per project tooling default; fall back to pip."""
    for cmd in (["uv", "pip", "freeze"], [sys.executable, "-m", "pip", "freeze"]):
        try:
            out = subprocess.run(
                cmd, capture_output=True, check=True,
                timeout=_SUBPROCESS_TIMEOUT_SEC,
            )
            return out.stdout
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return b""


def _host_info() -> dict[str, str]:
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "cpu": platform.machine(),
    }


# --------------------------------------------------------------------------- #
# Runtime-stack capture (4 fields)
#
# Boettiger (2015) ACM SIGOPS Oper. Syst. Rev. 49(1):71-79,
# doi:10.1145/2723872.2723882 — recreating a computational result requires
# the OS distribution + (when applicable) the container image digest, not
# just the source-code version and library list. The four helpers below
# capture exactly that: full sys.version, platform.platform() composite,
# container image digest (when probeable from inside the container), and
# the OS-release identifier.
# --------------------------------------------------------------------------- #

# /etc/os-release PRETTY_NAME line; quoted or unquoted value.
_OS_RELEASE_PRETTY_RE = re.compile(r'^\s*PRETTY_NAME\s*=\s*"?([^"\n]*)"?\s*$', re.MULTILINE)

# Container-id pattern in /proc/self/cgroup (Docker / Kubernetes layout):
# the trailing 64-hex segment after a slash. Used as a best-effort digest
# fallback when the engine does not expose the image digest directly.
_CGROUP_HEX_RE = re.compile(r"[0-9a-f]{64}")


def _runtime_python_version() -> str:
    """Full sys.version - typically multi-line; collapse to a single string."""
    return " ".join(sys.version.split())


def _runtime_platform() -> str:
    """platform.platform() - composite system/release/version/machine string."""
    return platform.platform()


def _runtime_container_digest() -> str | None:
    """Best-effort container image digest.

    Containers do not, in general, expose their own image digest from inside
    the running container without engine cooperation. This function probes
    the standard signals and returns the first usable identifier found:

      1. /proc/self/cgroup - the trailing 64-hex segment is the container
         ID under Docker and most Kubernetes runtimes. The container ID is
         distinct from the image digest, but it is a stable identifier of
         the running container instance.
      2. /run/.containerenv - Podman writes a `name=`/`id=` block here.
      3. The DOCKER_IMAGE_DIGEST env var if explicitly injected by the
         operator (no standard exists; this is opportunistic).

    Returns the digest string when a probe succeeds; None when no container
    is detected or no digest can be read. Detection of `/.dockerenv`,
    `/run/.containerenv`, or the KUBERNETES_SERVICE_HOST / DOCKER_CONTAINER
    env vars confirms we are inside a container; absence of all signals
    yields None.
    """
    # Operator-injected explicit digest takes precedence.
    explicit = os.environ.get("DOCKER_IMAGE_DIGEST") or os.environ.get("CONTAINER_IMAGE_DIGEST")
    if explicit:
        return explicit.strip() or None

    in_container = (
        Path("/.dockerenv").exists()
        or Path("/run/.containerenv").exists()
        or bool(os.environ.get("KUBERNETES_SERVICE_HOST"))
        or bool(os.environ.get("DOCKER_CONTAINER"))
    )

    # cgroup-based container-id probe (works even when in_container above
    # missed a non-standard runtime).
    try:
        cgroup_text = Path("/proc/self/cgroup").read_text(encoding="utf-8")
    except OSError:
        cgroup_text = ""
    if cgroup_text:
        match = _CGROUP_HEX_RE.search(cgroup_text)
        if match:
            return match.group(0)

    # Podman containerenv: parse `id=<digest>` if present.
    try:
        cenv = Path("/run/.containerenv").read_text(encoding="utf-8")
    except OSError:
        cenv = ""
    for line in cenv.splitlines():
        s = line.strip()
        if s.startswith("id=") or s.startswith("image_id="):
            value = s.split("=", 1)[1].strip().strip('"')
            if value:
                return value

    # In a container but no readable digest -> still return None per the
    # schema (a non-digest sentinel would lie about what we know).
    _ = in_container
    return None


def _runtime_os_release() -> str:
    """OS-release identifier as a single human-readable string.

    Linux: /etc/os-release PRETTY_NAME line (e.g. 'Ubuntu 22.04.3 LTS').
    Windows: platform.win32_ver() joined with spaces.
    macOS: platform.mac_ver() joined with spaces (version + dev_stage + machine).
    Falls back to '' when no source is readable.
    """
    system = platform.system()
    if system == "Linux":
        try:
            text = Path("/etc/os-release").read_text(encoding="utf-8")
        except OSError:
            text = ""
        m = _OS_RELEASE_PRETTY_RE.search(text)
        if m:
            return m.group(1).strip()
        # /etc/os-release missing or no PRETTY_NAME line - fall through.
    elif system == "Windows":
        # win32_ver -> (release, version, csd, ptype). Join non-empty parts.
        parts = [p for p in platform.win32_ver() if p]
        if parts:
            return "Windows " + " ".join(parts)
    elif system == "Darwin":
        # mac_ver -> (release, versioninfo, machine). versioninfo is a 3-tuple.
        release, versioninfo, machine = platform.mac_ver()
        flat = [release, *[v for v in versioninfo if v], machine]
        joined = " ".join(p for p in flat if p)
        if joined:
            return "macOS " + joined
    # Cross-platform last resort.
    return f"{system} {platform.release()}".strip()


def _runtime_info() -> dict[str, str | None]:
    return {
        "python_version": _runtime_python_version(),
        "platform": _runtime_platform(),
        "container_digest": _runtime_container_digest(),
        "os_release": _runtime_os_release(),
    }


# --------------------------------------------------------------------------- #
# Miscellaneous helpers
# --------------------------------------------------------------------------- #

def _posix(path: Path) -> str:
    return str(PurePosixPath(*Path(path).parts))


def _make_run_id() -> str:
    """ULID when available; uuid4 hex otherwise."""
    try:
        import ulid  # type: ignore
        return str(ulid.new())
    except ImportError:
        import uuid
        return uuid.uuid4().hex


def capture(
    *,
    phase: str,
    hypothesis_id: str = "n/a",
    rng_seed: int = 0,
    dataset_checksums: dict[str, str] | None = None,
    model_hash: str | None = None,
    config_resolved_sha256: str | None = None,
    env_id: str | None = None,
    paths: ProjectPaths | None = None,
    run_id: str | None = None,
) -> ReproLog:
    """Build a ReproLog from the current process state.

    Pure w.r.t. inputs given identical git/pip state - successive calls
    differ only in `timestamp_utc` (and auto-generated `run_id`).
    """
    paths = paths or ProjectPaths.discover()
    paths.ensure(paths.logs_reproducibility_env)

    freeze_bytes = _pip_freeze_bytes()
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    freeze_path = paths.logs_reproducibility_env / f"{freeze_sha}.txt"
    if not freeze_path.exists():
        freeze_path.write_bytes(freeze_bytes)

    uv_lock = paths.root / "uv.lock"
    lock_id = file_sha256(uv_lock) if uv_lock.is_file() else "no-uv-lock"

    return ReproLog(
        run_id=run_id or _make_run_id(),
        phase=phase,
        hypothesis_id=hypothesis_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        git_head=_git_head(paths.root),
        pip_freeze_sha256=freeze_sha,
        pip_freeze_path=_posix(freeze_path.relative_to(paths.root)),
        dataset_checksums=dict(dataset_checksums or {}),
        rng_seed=rng_seed,
        model_hash=model_hash,
        config_resolved_sha256=config_resolved_sha256,
        host=_host_info(),
        env_id=env_id or lock_id,
        runtime=_runtime_info(),
    )


def with_model_hash(log: ReproLog, model_hash: str) -> ReproLog:
    return replace(log, model_hash=model_hash)


# --------------------------------------------------------------------------- #
# Self-test entrypoint
# --------------------------------------------------------------------------- #

def _selftest() -> int:
    """Build -> write -> read -> verify round-trip. Exit 0 on success."""
    with tempfile.TemporaryDirectory() as td:
        # Override project-root discovery for the isolated fixture run.
        os.environ["CODEX_PROJECT_DIR"] = td
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
        paths = ProjectPaths.discover()
        paths.ensure(paths.logs_reproducibility_env)

        log = capture(
            phase="bootstrap",
            hypothesis_id="selftest",
            rng_seed=42,
            paths=paths,
        )
        out_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
        log.write(out_path)

        if not out_path.exists():
            print(f"FAIL: output file not created at {out_path}", file=sys.stderr)
            return 1

        if not ReproLog.verify(out_path):
            print(f"FAIL: round-trip verification failed for {out_path}", file=sys.stderr)
            return 2

        # Re-read and check field set
        re_read = ReproLog.read(out_path)
        d = re_read.to_dict()
        expected_fields = {
            "run_id", "phase", "hypothesis_id", "timestamp_utc", "git_head",
            "pip_freeze_sha256", "pip_freeze_path", "dataset_checksums",
            "rng_seed", "model_hash", "config_resolved_sha256", "host", "env_id",
            "runtime",
        }
        if set(d.keys()) != expected_fields:
            print(f"FAIL: field set mismatch. expected={expected_fields}, "
                  f"got={set(d.keys())}", file=sys.stderr)
            return 3

        # Validate pip_freeze_sha256 is exactly 64 hex chars
        if len(re_read.pip_freeze_sha256) != 64:
            print(f"FAIL: pip_freeze_sha256 is {len(re_read.pip_freeze_sha256)} chars; "
                  f"expected 64", file=sys.stderr)
            return 4

        # Validate host has 3 fields
        if set(re_read.host.keys()) != {"os", "python", "cpu"}:
            print(f"FAIL: host fields are {set(re_read.host.keys())}; "
                  f"expected {{os, python, cpu}}", file=sys.stderr)
            return 5

        # Validate runtime sub-object has 4 fields
        expected_runtime = {"python_version", "platform", "container_digest", "os_release"}
        if set(re_read.runtime.keys()) != expected_runtime:
            print(f"FAIL: runtime fields are {set(re_read.runtime.keys())}; "
                  f"expected {expected_runtime}", file=sys.stderr)
            return 6

        # Validate runtime types: python_version, platform, os_release are
        # non-empty strings; container_digest is str-or-None.
        for k in ("python_version", "platform", "os_release"):
            v = re_read.runtime[k]
            if not isinstance(v, str) or not v:
                print(f"FAIL: runtime.{k} is {v!r}; expected non-empty string",
                      file=sys.stderr)
                return 7
        cd = re_read.runtime["container_digest"]
        if cd is not None and not isinstance(cd, str):
            print(f"FAIL: runtime.container_digest is {cd!r}; expected str or None",
                  file=sys.stderr)
            return 8

        print(f"PASS: ReproLog round-trip OK at {out_path}")
        print(f"  run_id: {re_read.run_id}")
        print(f"  pip_freeze_sha256: {re_read.pip_freeze_sha256[:16]}... "
              f"({len(re_read.pip_freeze_sha256)} chars)")
        print(f"  env_id: {re_read.env_id}")
        print(f"  host: {re_read.host}")
        print(f"  runtime.platform: {re_read.runtime['platform']}")
        print(f"  runtime.os_release: {re_read.runtime['os_release']}")
        print(f"  runtime.container_digest: {re_read.runtime['container_digest']}")
        return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print("Usage: python emit_repro_log.py --selftest", file=sys.stderr)
    sys.exit(64)  # EX_USAGE
