---
name: audit-loop
description: Run the audit-remediate loop on the current deliverable (up to 3 rounds).
---

# audit-loop

## Usage

```
audit-loop [target file/glob]
```

If no target is supplied, infer the most recently modified non-test file set from `git diff`.

## Behavior

Invoke the [audit-remediate-loop](../audit-remediate-loop/SKILL.md) skill with:

- **Target.** The argument, or — if empty — the most recently modified non-test file set from `git diff`.
- **Acceptance criteria.** Inherit from the task spec in the current conversation.
- **Auditor selection.** Default to running `quant-auditor`, `literature-check`, and `reproducibility-verifier` in parallel on round 1. The audit-remediate-loop skill's routing rules add more auditors as needed (e.g., `code-reviewer` for code-bearing artifacts; `epi-auditor` for epi cwds in place of `quant-auditor`).
- **Exit.** On zero critical+major findings, or after round 3.
- **Audit trail.** Emit to `docs/audits/`.
