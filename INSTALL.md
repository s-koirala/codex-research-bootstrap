# Install

Authoritative install instructions live in [README.md](README.md) under the
"Install" section. This file remains as a redirect so existing inbound links
keep resolving.

Quick reference:

```
git clone <repo-url>
cd codex-research-bootstrap
./install.sh        # macOS / Linux
.\install.ps1       # Windows
```

The installer (`tools/install.py`) copies the bootstrap surface
(`skills/`, `.codex/agents/`, `hooks/`, `templates/`, `.codex/hooks.json`,
`.codex/config.toml`) into `$CODEX_HOME` (default `~/.codex/`).
Idempotent via SHA-256 content-hash skip; differing files are backed up
under `<target>/.bootstrap-backups/<timestamp>/` before overwrite. Append
`--dry-run` to preview.

After install, every non-trivial deliverable in any project that uses the
bootstrap passes through a six-branch parallel specialist audit
(reproducibility-verifier, code-reviewer, quant-auditor, epi-auditor,
format-auditor, literature-check; quant-auditor and epi-auditor are
mutually exclusive at the calculations branch, dispatched by cwd-glob) with
a three-round remediation cap. See [docs/SCOPE.md](docs/SCOPE.md) for the
canonical description.
