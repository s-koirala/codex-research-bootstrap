# Project Scope

## Mission

Provide an OpenAI Codex CLI bootstrap layer optimized for research
workflows in:

- Statistics and statistical inference
- Population science and epidemiology
- Public health
- Quantitative research analysis
- Results compilation and figure rendering
- Manuscript drafting and reporting-standards compliance

## Quality control

All non-trivial deliverables in this repository pass through an
**audit-remediate-loop**:

- Six-branch parallel specialist auditors:
  - **reproducibility-verifier** — pinned dependencies, seeds, dataset
    checksums, runnable entrypoint.
  - **code-reviewer** — idiom, style, design patterns, error handling,
    type hints, docstring completeness.
  - **quant-auditor** — statistical method fidelity, numerical
    correctness.
  - **epi-auditor** — DAG declaration, back-door adjustment-set
    selection, E-value sensitivity, STROBE / CONSORT / STARD / TRIPOD /
    PRISMA coverage.
  - **format-auditor** — magic-number policy, template-substitution
    completeness, citation-format consistency, docstring style.
  - **literature-check** — citation verification against primary sources.
- Quant-auditor and epi-auditor are mutually exclusive at the
  calculations branch: which one engages is determined by the cwd of
  the artifact under audit. Quant cwds activate `quant-auditor`;
  epi cwds activate `epi-auditor`. Cwd-glob patterns and methodology
  mandates are inlined in [AGENTS.md](../AGENTS.md) under the
  "Methodology mandates" section.
- Three-round remediation cap. Multi-agent self-consistency gains taper at
  moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751));
  three rounds is an operational choice balancing coverage against cost.
- Structured JSON findings, diff-based remediation, re-audit on each
  round.

## De-identification commitment

This repository is intended for distribution to research colleagues via
local clone. It contains no:

- Real names
- Pseudonyms tied to a single individual
- Personal email addresses
- OS usernames or workstation identifiers
- Institutional affiliations beyond those necessary for citation of
  external work

Contributors are expected to maintain this commitment in any pull request
or fork that re-merges upstream.

## Reporting standards (domain-conditional)

| Study type | Standard |
|---|---|
| Observational | STROBE |
| Randomized controlled trial | CONSORT |
| Diagnostic accuracy | STARD |
| Prediction model | TRIPOD |
| Systematic review / meta-analysis | PRISMA |

The applicable standard is declared at the top of each analysis document.

## Reproducibility envelope

Every bootstrap, backtest, or inference run logs:

- Git HEAD of the repository
- `pip freeze` of the active Python environment
- Dataset checksum(s)
- RNG seed
- Model commit hash (where applicable)

Provenance is emitted as a ReproLog JSON record and threaded into commits
via Conventional Commits trailers.
