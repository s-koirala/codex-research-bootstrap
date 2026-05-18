---
name: audit-remediate-loop
description: Run the research→audit→remediate agentic QC pattern with a 3-round cap and structured findings. Invoke for any non-trivial implementation or analysis deliverable.
---

# Audit-Remediate Loop

## When to invoke
Any non-trivial deliverable: new statistical method, new module, new analysis notebook, revised claim. Skip for formatting, renames, or <20-line patches.

## Cap
Max 3 audit rounds. Empirical basis: self-consistency gains via multi-path sampling taper at moderate sample counts ([arXiv 2511.00751](https://arxiv.org/abs/2511.00751); the paper studies single-model multi-path sampling, not multi-agent ensembles, but the diminishing-returns direction is the load-bearing inference for the cap). 3 rounds is an operational cost/coverage choice, not a result in the cited paper. If residuals remain after round 3, surface them to the user — do not continue silently.

## Loop structure

### Round N (N ∈ {1, 2, 3})

1. **Produce/revise.** The lead agent (main session) produces or revises the artifact.
2. **Audit — spawn specialist auditors in parallel.** Brief each with:
   - The artifact path(s).
   - The task spec and acceptance criteria.
   - `AGENTS.md` + relevant cwd-scoped methodology mandates inlined in AGENTS.md.
   - A directive to return findings only as structured JSON:
     ```
     { "round": N,
       "findings": [
         {"severity": "critical|major|minor", "location": "file:line",
          "issue": "...", "evidence": "...", "fix": "..."}
       ],
       "residual_risk": "..." }
     ```
   Spawn all relevant auditors in a single message (parallel subagent invocations) so they run concurrently. See §"Auditor selection" below.
3. **Triage.** Drop `minor` findings unless the user's task specifically invites polish. `critical` blocks progression; `major` is remediated this round.
4. **Remediate.** Apply fixes. Each fix references the finding ID in its commit message or doc note.
5. **Exit check.** If `findings == []` or only `minor` remain → exit. Otherwise increment N.

### Post-loop
- Emit `audit_trail_{YYYY-MM-DD}_{slug}.md` under `docs/audits/` listing every finding + disposition + round number.
- Record final residual risk in the project README or analysis doc.

## Auditor selection — 6 specialist branches (quant-auditor and epi-auditor mutually exclusive at the calculations branch)

Pattern: parallel-specialist-ensemble ("Mixture of Agents" per [Wang et al. 2024 arXiv:2406.04692](https://arxiv.org/abs/2406.04692); multi-agent debate per [Du et al. 2023 arXiv:2305.14325](https://arxiv.org/abs/2305.14325)). Each auditor covers a non-overlapping concern; mixed-concern artifacts get multiple auditors spawned in parallel. The calculations branch holds two mutually exclusive auditors — quant-auditor for quant cwds, epi-auditor for epi cwds — so any one run spawns at most five auditors concurrently, drawn from the six listed below.

| Concern (calculations + research + reproducibility + coding + formatting) | Auditor | Cwd scoping |
|---|---|---|
| **Calculations** (statistical method fidelity, numerical correctness) | [`quant-auditor`](../../.codex/agents/quant-auditor.toml) | quant cwds (e.g., `**/backtest*/`, `**/factor*/`, `**/signal*/`, `**/strategy*/`) |
| **Calculations** (epi causal inference, E-value, STROBE/CONSORT/STARD/TRIPOD/PRISMA coverage) | [`epi-auditor`](../../.codex/agents/epi-auditor.toml) | epi cwds (e.g., `**/epidemiolog*/`, `**/clinical*/`, `**/cohort*/`, `**/case-control*/`, `**/RCT*/`, `**/diagnostic*/`) |
| **Research** (citation validity, primary-source verification, method-attribution accuracy) | [`literature-check`](../../.codex/agents/literature-check.toml) | cwd-agnostic |
| **Reproducibility** (ReproLog completeness, atomic-write spec, git HEAD logging, replay anchors) | [`reproducibility-verifier`](../../.codex/agents/reproducibility-verifier.toml) | cwd-agnostic |
| **Coding** (Python/general code quality, idiom, types, error handling, design patterns) | [`code-reviewer`](../../.codex/agents/code-reviewer.toml) | cwd-agnostic |
| **Formatting** (magic-numbers compliance, identity hygiene, template substitution, citation-format consistency, filename convention) | [`format-auditor`](../../.codex/agents/format-auditor.toml) | cwd-agnostic |

### Routing rules

- **Code-bearing artifacts** (`.py`, `.ipynb`): always include `code-reviewer`.
- **Statistical analyses / backtests / inferences**: include `quant-auditor` (quant) OR `epi-auditor` (epi).
- **Artifacts with citations**: include `literature-check`.
- **Artifacts emitting ReproLog / dataset manifest / commits with provenance trailers**: include `reproducibility-verifier`.
- **Anything destined for `~/.codex/` or with magic-number / identity-hygiene exposure**: include `format-auditor`.
- **Quant vs epi**: never both for the calculations branch. Cwd-glob dispatch determines which one engages.

### Empirical basis for parallel-specialist over single-auditor

Single-auditor approaches have known coverage gaps. [Wang et al. 2024 Mixture-of-Agents](https://arxiv.org/abs/2406.04692) Table 3 (proposer-count ablation) reports AlpacaEval 2.0 scores rising from 47.8% (1 proposer) to 61.3% (6 proposers) — a +13.5 pp gain — while characterizing MoA's MT-Bench gains as "relatively incremental" due to ceiling effects. The general direction (specialist ensembles outperform a single agent on tasks with diverse rubrics) supports parallel branching. Specialist branches reduce the cross-domain dilution that occurs when one agent reasons over heterogeneous concerns (code + citations + repro + format).

## Empirical justification
- Single-shot code-generation baselines are weak on statistical code: DS-1000 Pandas Pass@1 = 0.265 (Codex-002; [arXiv 2211.11501](https://arxiv.org/abs/2211.11501)).
- Research-grade: SciCode main problems — a frontier model (4.6% Pass@1 on SciCode main, [arXiv 2407.13168](https://arxiv.org/abs/2407.13168)).
- Self-consistency via multi-path sampling improves chain-of-thought reasoning: +17.9 pp GSM8K ([Wang et al. 2022, arXiv 2203.11171](https://arxiv.org/abs/2203.11171)). Self-refinement / critique-and-revise is a distinct pattern ([Madaan et al. 2023 SELF-REFINE, arXiv 2303.17651](https://arxiv.org/abs/2303.17651)); both directions support iterative audit-remediate beyond single-shot generation.
Audit is empirically required; cap reflects diminishing-returns evidence, not a result for n=3 specifically.
