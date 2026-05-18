# ADR 0001: Repository scope and naming

- **Status**: Accepted
- **Date**: 2026-05-18

## Context

A pre-existing Claude Code customization layer provides research-grade
workflows for statistics, population science, public health, and academic
publishing. The maintainer wants to provide a parallel layer for the
OpenAI Codex CLI so that colleagues with Codex installed can clone a
single repository and receive an equivalent setup.

The pre-existing Claude Code layer is identity-bound: it contains
references to the original maintainer's pseudonym, personal commit
metadata, and workstation-specific paths. The Codex layer must be
de-identified so it can be cloned by multiple research colleagues without
leaking individual-contributor data.

## Decision

A new repository `codex-research-bootstrap` is created at
`~/code/codex-research-bootstrap/`. It is scoped to research workflows in
statistics, population science, public health, manuscript drafting, and
results compilation, with the audit-remediate-loop as the default
quality-control pattern.

The repository is de-identified at scaffold time and de-identification is
enforced going forward (no real names, pseudonyms, personal emails, OS
usernames, or workstation identifiers in committed content).

The repository is self-contained: the audit-remediate-loop skill and any
referenced subagents, hooks, or templates live inside the repository
rather than in the maintainer's personal `~/.claude/`, so a colleague
clone yields a functioning setup without external dependencies beyond
Codex CLI itself and the declared MCP servers.

## Consequences

- Research artifacts, decision records, and audit-round logs accumulate
  inside the new repository rather than in `~/.claude/`.
- Colleagues can clone a single repository to receive a working Codex
  setup, including the audit-remediate-loop skill itself.
- The repository's `AGENTS.md` and skills point at the repository's own
  bundled components, not at any external directory.
- Audit-round logs are gitignored (`logs/`, `audit_trail_*.md`,
  `audit_round_*.md`) so they remain local-only and do not ship with the
  public clone.
- Git authorship metadata for this repository must use a placeholder
  identity, not the maintainer's global git configuration.

## Alternatives considered

- **Edit the existing `~/.claude/` setup in place.** Rejected:
  de-identification is harder when the starting point already has
  identity references throughout, and the personal setup is not intended
  for cloning by other contributors.
- **Generic name (e.g., `codex-template`).** Rejected: a domain-specific
  name signals scope clearly to colleagues evaluating whether the
  template fits their work.
- **Reference the source skills from `~/.claude/skills/` rather than
  bundling them.** Rejected: a colleague clone would be non-functional
  without an identical maintainer-side setup, which defeats the purpose
  of the shareable repository.
