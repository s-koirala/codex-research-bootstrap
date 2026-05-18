---
name: reproduce
description: Spawn the reproducibility-verifier agent against the current project.
---

# reproduce

## Usage

```
reproduce [project root]
```

Default target: the current cwd.

## Behavior

Spawn the [`reproducibility-verifier`](../../.codex/agents/reproducibility-verifier.toml) subagent against the supplied project root (or cwd).

Brief it with:

- Project root path.
- Any declared entrypoint (Makefile, nox, Justfile, package.json scripts).
- The expected runtime (quick smoke vs full reproduction).

Return its JSON verdict verbatim, then propose remediation commits for any `fail` or `partial` checks.
