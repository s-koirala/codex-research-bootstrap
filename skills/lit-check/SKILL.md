---
name: lit-check
description: Spawn the literature-check agent on the current artifact.
---

# lit-check

## Usage

```
lit-check [file/glob]
```

Default target: the most recently modified `.md` / `.ipynb` / `.py` files in the current project.

## Behavior

Spawn the [`literature-check`](../../.codex/agents/literature-check.toml) subagent on the target.

Return the JSON verdict. Block merge or publication on any `critical` or `major` finding.
