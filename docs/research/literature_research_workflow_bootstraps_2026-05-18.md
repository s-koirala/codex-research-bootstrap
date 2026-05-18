# Literature: Research-Workflow Bootstraps, Audit-Remediate Antecedents, and Workflow Tooling

## Provenance

- Date: 2026-05-18.
- Author: anonymous contributor (de-identified per [docs/decisions/0001-repo-scope-and-naming.md](../decisions/0001-repo-scope-and-naming.md)).
- Scope: literature review grounding the design of this repository (a research-focused
  Codex CLI bootstrap layer) in three threads — reproducibility-focused CLI bootstraps,
  audit-remediate-loop antecedents in software engineering and AI agents, and
  research-workflow tooling patterns.
- Verification protocol: every citation below was checked against the publisher
  page, the arXiv abstract, or an indexing service (PubMed, dblp, JOSS). Citations
  the verification could not resolve are marked `[UNVERIFIED]` with the obstacle
  recorded in [Open questions](#open-questions). Inline citations follow the
  first-author + year convention; full bibliographic detail is in
  [References](#references).
- Evidence hierarchy: peer-reviewed > official documentation > professional
  standards > vetted technical forums. Forum sources are not used.

## Scope and method

The repository in question scaffolds a Codex CLI workflow for statistical,
epidemiological, and quantitative research — see [docs/SCOPE.md](../SCOPE.md). Two
design commitments make the literature load-bearing:

1. A six-branch parallel-specialist audit (reproducibility-verifier,
   code-reviewer, quant-auditor, epi-auditor, format-auditor,
   literature-check; quant-auditor and epi-auditor are mutually
   exclusive at the calculations branch, dispatched by cwd-glob) with a
   three-round remediation cap.
2. A reproducibility envelope of {git HEAD, `pip freeze`, dataset checksum,
   RNG seed, model commit hash}, threaded into commits as conventional-commits
   trailers.

This review evaluates whether each commitment has empirical support and where
the established literature points to refinements. Method: prior-art review by
forward-search from canonical anchor papers in each thread; verification of
each anchor by retrieving the publisher record or arXiv abstract.

## Thread 1 — Reproducibility bootstraps

### Definitions

The National Academies (NASEM 2019) distinguish *reproducibility* (same data
and code yield the same results) from *replicability* (independent data or
methods yield consistent findings); the report explicitly observes that
"unlike the typical expectation of reproducibility between two computations,
expectations about replicability are more nuanced" (NASEM 2019, DOI
[10.17226/25303](https://doi.org/10.17226/25303)). This bootstrap targets the
former: bit-level computational reproducibility.

### Minimal envelope in the canonical literature

Sandve et al. 2013 in PLOS Computational Biology give a ten-rule template that
remains the most-cited operational checklist for reproducible computation
(DOI [10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285)).
Rules 1, 3, 4, 6, and 10 map directly onto the envelope this repository
declares:

| Sandve 2013 rule | This repo's envelope element |
|---|---|
| Rule 1: track how every result was produced | ReproLog JSON record |
| Rule 3: archive exact versions of all external programs | `pip freeze` capture |
| Rule 4: version-control all custom scripts | git HEAD capture |
| Rule 6: note random seeds for analyses with randomness | RNG seed capture |
| Rule 10: provide public access to scripts, runs, results | Conventional Commits trailers |

Wilson et al. 2017 PLOS Computational Biology ("Good Enough Practices in
Scientific Computing", DOI
[10.1371/journal.pcbi.1005510](https://doi.org/10.1371/journal.pcbi.1005510))
generalize the Sandve rules into six practice families (data management,
software, collaboration, project organization, change tracking, manuscript
writing). The "explicitly document software dependencies" and "use version
control" recommendations are this repo's `pip freeze` + git HEAD captures.
Sandve and Wilson do not specify dataset checksums, but Wilson 2017 recommends
"deposit data in repositories that assign DOIs", which implicitly demands
a content identifier — the SHA-256 dataset checksum this repo logs is a
defensible local-stage substitute.

Wilkinson et al. 2016 *Scientific Data* ("The FAIR Guiding Principles for
scientific data management and stewardship", DOI
[10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)) shift the
target from internal reproducibility to data-asset stewardship: Findable,
Accessible, Interoperable, Reusable. FAIR is data-side and orthogonal to a
CLI-bootstrap envelope but constrains how dataset checksums and identifiers
should be exposed when a project is published.

Marwick, Boettiger, Mullen 2018 *American Statistician* ("Packaging Data
Analytical Work Reproducibly Using R (and Friends)", DOI
[10.1080/00031305.2017.1375986](https://doi.org/10.1080/00031305.2017.1375986))
operationalize the *research compendium*: a single directory tree with a
manifest, data, code, and outputs that can be cited, archived, and re-run.
The compendium is the unit this repo treats as the audit subject.

Blischak, Carbonetto, Stephens 2019 *F1000Research* ("Creating and sharing
reproducible research code the workflowr way", DOI
[10.12688/f1000research.20843.1](https://doi.org/10.12688/f1000research.20843.1))
specifies a four-element workflow: Git, R Markdown, automatic reproducibility
checks, and a generated website. The "automatic reproducibility checks"
element — each report stamped with seed, session info, git commit at render
time — is the closest published precedent for the ReproLog this repo emits.

The Turing Way Community (DOI
[10.5281/zenodo.3233853](https://doi.org/10.5281/zenodo.3233853), concept DOI
resolving to current version 1.2.3 as of April 2025) is the most thorough
community handbook on reproducible, ethical, and collaborative research and
informs the de-identification posture documented in
[docs/decisions/0001-repo-scope-and-naming.md](../decisions/0001-repo-scope-and-naming.md).

Stodden, Seiler, Ma 2018 PNAS provide the empirical case for envelope
machinery: they requested data and code for 204 *Science* papers published
after that journal's reproducibility policy went into effect and obtained
artifacts for 44%, successfully reproducing findings for 26% (DOI
[10.1073/pnas.1708290115](https://doi.org/10.1073/pnas.1708290115)). Voluntary
post-publication policies are necessary but insufficient; structural capture
at run time — what this repo's envelope automates — is the proposed remedy.

### Envelope adequacy verdict

The five-element envelope declared in [SCOPE.md](../SCOPE.md) is
consistent with Sandve 2013 rules 1, 3, 4, 6, 10 and with Wilson 2017's
software-dependency recommendation. One gap: NASEM 2019 and several FAIR
implementations (Wilkinson 2016) note that container hash or OS/runtime
fingerprint matters for results that depend on numerical libraries; Boettiger
2015 (DOI [10.1145/2723872.2723882](https://doi.org/10.1145/2723872.2723882))
argues that without a runtime image, even pinned-version package lists can
produce non-deterministic numerics. The repo's "model commit hash (where
applicable)" slot can absorb a container digest; it should be made explicit.

## Thread 2 — Audit-remediate antecedents

### Multi-sample / multi-agent inference patterns

Wang et al. 2022 *Self-Consistency Improves Chain of Thought Reasoning in
Language Models* (arXiv
[2203.11171](https://arxiv.org/abs/2203.11171)) introduces sampling-and-vote:
sample N reasoning paths, marginalize, take the modal final answer. Reports
substantial gains on GSM8K (+17.9% over greedy CoT) and other arithmetic /
commonsense benchmarks.

Madaan et al. 2023 *Self-Refine: Iterative Refinement with Self-Feedback*
(arXiv [2303.17651](https://arxiv.org/abs/2303.17651)) is a distinct pattern:
one model generates output, critiques its own output, revises. Reports ~20%
absolute improvement across seven tasks. This is critique-and-revise, not
sample-and-vote — they compose but address different failure modes.

Du et al. 2023 *Improving Factuality and Reasoning in Language Models through
Multiagent Debate* (arXiv
[2305.14325](https://arxiv.org/abs/2305.14325)): multiple instances propose
and debate responses across rounds and converge on a common answer; gains on
math and factuality benchmarks.

Wang et al. 2024 *Mixture-of-Agents Enhances Large Language Model
Capabilities* (arXiv [2406.04692](https://arxiv.org/abs/2406.04692)) is the
explicit empirical basis for layered specialist ensembles. Reports MoA
reaching 65.1% on AlpacaEval 2.0 versus GPT-4 Omni at 57.5% using only
open-source LLMs.

Zheng et al. 2023 *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*
(arXiv [2306.05685](https://arxiv.org/abs/2306.05685)) shows LLM judges match
human preference rankings at >80% agreement (matching inter-human agreement)
once position and verbosity biases are controlled. This underwrites the
audit-remediate pattern of letting one model adjudicate another's output.

Bai et al. 2022 *Constitutional AI: Harmlessness from AI Feedback* (arXiv
[2212.08073](https://arxiv.org/abs/2212.08073)) operationalizes
AI-supervising-AI through a written constitution that drives both critique
and reward modeling (RLAIF). It is the precedent for handing each audit
branch a rule-set rather than free-form criticism.

### The load-bearing citation in SCOPE.md

[SCOPE.md](../SCOPE.md) cites arXiv
[2511.00751](https://arxiv.org/abs/2511.00751) as the empirical basis for the
three-round remediation cap. Verification of the abstract: the paper, Loo
2025 *Self-Consistency Is Losing Its Edge: Diminishing Returns and Rising
Costs in Modern LLMs*, reports +0.4% accuracy on HotpotQA across 20 sampled
reasoning paths and +1.6% on MATH-500, with token cost scaling near-linearly
in sample count. It concludes performance "plateaued early and in some
configurations declined at high sample counts" and recommends "reserving
multi-path sampling for problems that demonstrably exceed a model's
single-pass reliability".

The paper does **not** prescribe any specific cap (three rounds or otherwise)
and does not test multi-agent audit-remediate workflows. Its operative claim
is selective application, not a fixed-N truncation. The SCOPE.md justification
("multi-agent self-consistency gains taper at moderate sample counts") is a
fair gloss on the paper's *direction* but overstates the specificity of its
*prescription*. The three-round cap is an operational choice; the paper
provides indirect support (diminishing returns are real) but no quantitative
basis for "three" as the inflection point. This is acknowledged honestly in
the SCOPE.md text ("three is an operational choice balancing coverage against
cost"), and the qualifier is appropriate.

### Classical program-repair antecedents

The six-branch audit-remediate-loop has structural parallels in classical
automated program repair:

- Le Goues et al. 2012 *GenProg: A Generic Method for Automatic Software
  Repair* (IEEE TSE, DOI
  [10.1109/TSE.2011.104](https://doi.org/10.1109/TSE.2011.104)) — genetic
  programming over test-passing patch candidates; 16 programs / 1.25 M LOC,
  eight defect classes, 357-second average repair.
- Urli, Yu, Seinturier, Monperrus 2018 *How to Design a Program Repair Bot?
  Insights from the Repairnator Project* (ICSE-SEIP, DOI
  [10.1145/3183519.3183540](https://doi.org/10.1145/3183519.3183540)) —
  CI-driven autonomous patch-generation bot.
- Marginean et al. 2019 *SapFix: Automated End-to-End Repair at Scale*
  (ICSE-SEIP, DOI
  [10.1109/ICSE-SEIP.2019.00039](https://doi.org/10.1109/ICSE-SEIP.2019.00039))
  — first industrial deployment of end-to-end automated fixing across six
  Facebook production systems totaling tens of millions of LOC.

These antecedents share the audit-then-remediate cycle but operate on a single
critic (the test suite). The novelty in an LLM-era audit-remediate-loop is
parallel *specialist* critics with non-overlapping competences — closer in
spirit to Wang 2024 Mixture-of-Agents than to GenProg.

### Six-branch design verdict

The six-branch parallel specialist ensemble is well-supported by Wang 2024
(specialist ensembles produce gains over single-agent inference) and Du 2023
(multiple instances reduce hallucination via mutual critique). Each branch
mapping a distinct rule set (reproducibility, code style, statistics-quant or
statistics-epi, format, literature) is consistent with Bai 2022's
constitutional-AI principle:
explicit rules outperform free-form critique.

### Three-round cap defensibility

Loo 2025 (arXiv 2511.00751) shows that beyond a small number of additional
samples, accuracy gains are sub-percentage while cost grows linearly; it
therefore provides directional support for an early cap but not for *three*
specifically. The cap as currently framed is defensible as an operational
heuristic but not as an empirically tuned number. An audit log of round-count
versus marginal-finding-rate (logging when round 3 actually changes the
deliverable versus when it does not) would let the cap be data-tuned later.
This is the same logic the user-level CLAUDE.md applies to "zero arbitrary
thresholds or magic numbers": the round count should be a tunable subject to
empirical revision once enough audit-trail data accumulates.

## Thread 3 — Workflow tooling

### Pipeline DAG runners

The dominant pattern is a DAG runner that maps targets to commands and skips
re-execution when inputs and code are unchanged:

- Landau 2018 JOSS *drake* (DOI
  [10.21105/joss.00550](https://doi.org/10.21105/joss.00550)) and its
  successor Landau 2021 JOSS *targets* (DOI
  [10.21105/joss.02959](https://doi.org/10.21105/joss.02959)) implement a
  function-oriented Make-like DAG in R with a content-addressed cache
  keyed on input hash, code hash, and dependency set.
- Mölder et al. 2021 *Sustainable data analysis with Snakemake*
  (F1000Research, DOI
  [10.12688/f1000research.29032.2](https://doi.org/10.12688/f1000research.29032.2))
  uses Python-defined rules with conda/container integration and
  scatter-gather. The paper's framing — reproducibility, adaptability,
  transparency — is broader than bit-level reproducibility alone and matches
  the audit philosophy here.
- Di Tommaso et al. 2017 *Nextflow enables reproducible computational
  workflows* (Nature Biotechnology, DOI
  [10.1038/nbt.3820](https://doi.org/10.1038/nbt.3820)) uses
  channel-based DSL and container-per-process; argues containers are
  essential for numerical stability on heterogeneous HPC.
- Crusoe et al. 2022 *Methods Included: Standardizing Computational Reuse
  and Portability with the Common Workflow Language* (Communications of the
  ACM, DOI [10.1145/3486897](https://doi.org/10.1145/3486897)) — open
  workflow-description standard for inter-engine portability.

### Literate-document engines

Quarto (official site [quarto.org](https://quarto.org/), accessed 2026-05-18)
is the current open-source successor to R Markdown: Pandoc-backed,
multi-language (Python, R, Julia, Observable), parameterized reports,
multiple output formats (HTML, PDF via LaTeX or Typst, Word, Revealjs).
workflowr (Blischak 2019, above) sits on top of R Markdown with a
reproducibility-check layer.

### Environment pinning

Two ecosystem responses to "the same code on a different machine produced
different numbers":

- renv (Ushey & Wickham, CRAN package
  [renv](https://cran.r-project.org/package=renv); documentation at
  [rstudio.github.io/renv](https://rstudio.github.io/renv/), accessed
  2026-05-18) — R project-local libraries pinned in `renv.lock`.
- conda-lock ([github.com/conda/conda-lock](https://github.com/conda/conda-lock),
  accessed 2026-05-18) — multi-platform conda-environment lockfile.

Boettiger 2015 *An introduction to Docker for reproducible research* (ACM
SIGOPS Operating Systems Review, DOI
[10.1145/2723872.2723882](https://doi.org/10.1145/2723872.2723882)) is the
canonical argument that even pinned package lists are insufficient for
heterogeneous OS/runtime stacks and that container images are the
appropriate substrate.

### Empirical case for workflow capture

Stodden 2018 PNAS (cited above) showed that journal-policy-only enforcement
yielded 26% reproduction success on a 204-paper *Science* sample. The implied
remedy is run-time capture rather than after-the-fact request — exactly the
function of a workflow runner and the ReproLog this repo emits.

### Transferable to a Codex CLI bootstrap

| Pattern | Source | Transfer to this repo |
|---|---|---|
| Content-addressed cache | targets, drake, Snakemake | Per-skill manifest with input/output hashes for audit-trail dedup |
| Declarative DAG | Snakemake, Nextflow, CWL | Out of scope: chat-driven CLI does not need a full DAG engine; AGENTS.md hierarchy is the dependency mechanism |
| Container/environment pinning | renv, conda-lock, Boettiger 2015 | Container digest slot in ReproLog; current envelope has `pip freeze` only |
| Parameterized reports | Quarto, workflowr | Templated manuscript skills should accept parameters and emit a render-log sidecar |
| Run-log sidecars | workflowr's `_workflowr.yml`, Snakemake's report | Already implemented as ReproLog JSON |
| Multi-platform reproducibility | CWL, Nextflow | Future work; not P0 for a single-platform CLI bootstrap |

## Synthesis — implications for this repo

### Reproducibility envelope adequacy

The five-element envelope ({git HEAD, `pip freeze`, dataset checksum, RNG
seed, model commit hash}) covers Sandve 2013 rules 1, 3, 4, 6, 10. One
defensible upgrade: make the "model commit hash" slot explicit about
container or runtime image digest when the run executes inside one (per
Boettiger 2015). A second: FAIR-style persistent identifiers for any
externally published dataset, beyond the local checksum (Wilkinson 2016).

### Three-round cap empirical basis

Loo 2025 (arXiv 2511.00751) supports the *direction* of an early cap — gains
plateau, sometimes turn negative beyond a small number of additional samples
— but does not prescribe three rounds specifically. The cap should be treated
as a tunable subject to revision once round-count vs marginal-finding-rate
data accumulates from actual audit-trail logs. Adopting a
data-driven-thresholds posture (per user-level CLAUDE.md) means the cap
should be revisited once N audit logs exist; pre-registering the inflection
criterion now is appropriate.

### Patterns to import from workflow tooling

1. **Per-skill manifest with content hashes** (from targets, drake) — each
   skill execution emits a record keyed on input hash + skill version, so
   re-running an unchanged audit branch on unchanged inputs can be skipped
   or referenced.
2. **Container digest in the envelope** (from Boettiger 2015, Nextflow) — add
   to the ReproLog schema as an optional field that is populated whenever
   the run executes inside a container.
3. **Render-log sidecars for manuscripts** (from workflowr, Quarto) — the
   manuscript-render skill should emit a sidecar capturing pandoc version,
   input SHA-256, output SHA-256, citation-cache SHA-256.
4. **Explicit "skipped because unchanged" branch in audit logs** (from
   Snakemake's `--list-changes`) — supports audit deduplication.

### Patterns not to import

- A full DAG engine. The audit-remediate-loop is a finite, structured pattern
  with a known shape; Snakemake-style declarative DAGs add machinery that a
  chat-driven CLI does not need.
- Multi-platform workflow portability specs (CWL) — premature optimization
  for a single-platform clone-and-run bootstrap.

## Open questions

1. **Three-round cap calibration.** Once the audit trail accumulates, fit
   the empirical relationship between round count and marginal finding
   discovery. The cap is currently a heuristic; it should be tuned.
2. **Container digest field.** Should the ReproLog schema reserve a
   `container_digest` field now, or be extended later when container runs
   are common?
3. **Audit-branch competence overlap.** Wang 2024 Mixture-of-Agents reports
   gains from diverse specialists, but no quantitative analysis exists for
   the specific six-branch composition here. A retrospective study of
   audit findings by branch would identify gaps and redundancies.
4. **Turing Way version pinning.** This review cites the Turing Way concept
   DOI; deliverables that quote a specific section should pin the
   version-specific DOI.
5. **Codex-CLI-specific lifecycle.** The
   [codex feature map](codex_feature_map_2026-05-18.md) flags that Codex
   `Stop` fires per turn rather than per session. The reproducibility
   literature reviewed here (Sandve, Wilson, Blischak) assumes per-run
   capture; a per-turn capture has different debounce semantics and merits
   a dedicated design note.

## References

- Bai, Y., Kadavath, S., Kundu, S., et al. 2022. Constitutional AI:
  Harmlessness from AI Feedback. arXiv:2212.08073.
  <https://arxiv.org/abs/2212.08073>.
- Blischak, J. D., Carbonetto, P., Stephens, M. 2019. Creating and sharing
  reproducible research code the workflowr way. *F1000Research* 8:1749. DOI
  [10.12688/f1000research.20843.1](https://doi.org/10.12688/f1000research.20843.1).
- Boettiger, C. 2015. An introduction to Docker for reproducible research.
  *ACM SIGOPS Operating Systems Review* 49(1):71–79. DOI
  [10.1145/2723872.2723882](https://doi.org/10.1145/2723872.2723882).
- Crusoe, M. R., Abeln, S., Iosup, A., et al. 2022. Methods Included:
  Standardizing Computational Reuse and Portability with the Common Workflow
  Language. *Communications of the ACM* 65(6):54–63. DOI
  [10.1145/3486897](https://doi.org/10.1145/3486897).
- Di Tommaso, P., Chatzou, M., Floden, E. W., et al. 2017. Nextflow enables
  reproducible computational workflows. *Nature Biotechnology* 35:316–319.
  DOI [10.1038/nbt.3820](https://doi.org/10.1038/nbt.3820).
- Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., Mordatch, I. 2023.
  Improving Factuality and Reasoning in Language Models through Multiagent
  Debate. arXiv:2305.14325. <https://arxiv.org/abs/2305.14325>.
- Landau, W. M. 2018. The drake R package: a pipeline toolkit for
  reproducibility and high-performance computing. *Journal of Open Source
  Software* 3(21):550. DOI
  [10.21105/joss.00550](https://doi.org/10.21105/joss.00550).
- Landau, W. M. 2021. The targets R package: a dynamic Make-like
  function-oriented pipeline toolkit for reproducibility and high-performance
  computing. *Journal of Open Source Software* 6(57):2959. DOI
  [10.21105/joss.02959](https://doi.org/10.21105/joss.02959).
- Le Goues, C., Nguyen, T., Forrest, S., Weimer, W. 2012. GenProg: A Generic
  Method for Automatic Software Repair. *IEEE Transactions on Software
  Engineering* 38(1):54–72. DOI
  [10.1109/TSE.2011.104](https://doi.org/10.1109/TSE.2011.104).
- Loo, C. 2025. Self-Consistency Is Losing Its Edge: Diminishing Returns and
  Rising Costs in Modern LLMs. arXiv:2511.00751.
  <https://arxiv.org/abs/2511.00751>.
- Madaan, A., Tandon, N., Gupta, P., et al. 2023. Self-Refine: Iterative
  Refinement with Self-Feedback. arXiv:2303.17651.
  <https://arxiv.org/abs/2303.17651>.
- Marginean, A., Bader, J., Chandra, S., Harman, M., Jia, Y., Mao, K.,
  Mols, A., Scott, A. 2019. SapFix: Automated End-to-End Repair at Scale.
  *ICSE-SEIP*. DOI
  [10.1109/ICSE-SEIP.2019.00039](https://doi.org/10.1109/ICSE-SEIP.2019.00039).
- Marwick, B., Boettiger, C., Mullen, L. 2018. Packaging Data Analytical
  Work Reproducibly Using R (and Friends). *The American Statistician*
  72(1):80–88. DOI
  [10.1080/00031305.2017.1375986](https://doi.org/10.1080/00031305.2017.1375986).
- Mölder, F., Jablonski, K. P., Letcher, B., et al. 2021. Sustainable data
  analysis with Snakemake. *F1000Research* 10:33. DOI
  [10.12688/f1000research.29032.2](https://doi.org/10.12688/f1000research.29032.2).
- National Academies of Sciences, Engineering, and Medicine. 2019.
  Reproducibility and Replicability in Science. Washington, DC: The
  National Academies Press. DOI
  [10.17226/25303](https://doi.org/10.17226/25303).
- Sandve, G. K., Nekrutenko, A., Taylor, J., Hovig, E. 2013. Ten Simple
  Rules for Reproducible Computational Research. *PLOS Computational
  Biology* 9(10):e1003285. DOI
  [10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).
- Stodden, V., Seiler, J., Ma, Z. 2018. An empirical analysis of journal
  policy effectiveness for computational reproducibility. *PNAS*
  115(11):2584–2589. DOI
  [10.1073/pnas.1708290115](https://doi.org/10.1073/pnas.1708290115).
- The Turing Way Community. 2025 (concept DOI; current version 1.2.3,
  April 2025). The Turing Way: A handbook for reproducible, ethical and
  collaborative research. Zenodo. DOI
  [10.5281/zenodo.3233853](https://doi.org/10.5281/zenodo.3233853).
- Urli, S., Yu, Z., Seinturier, L., Monperrus, M. 2018. How to Design a
  Program Repair Bot? Insights from the Repairnator Project. *ICSE-SEIP*.
  DOI [10.1145/3183519.3183540](https://doi.org/10.1145/3183519.3183540).
- Wang, J., Wang, J., Athiwaratkun, B., Zhang, C., Zou, J. 2024.
  Mixture-of-Agents Enhances Large Language Model Capabilities.
  arXiv:2406.04692. <https://arxiv.org/abs/2406.04692>.
- Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S.,
  Chowdhery, A., Zhou, D. 2022. Self-Consistency Improves Chain of Thought
  Reasoning in Language Models. arXiv:2203.11171.
  <https://arxiv.org/abs/2203.11171>.
- Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., et al. 2016. The
  FAIR Guiding Principles for scientific data management and stewardship.
  *Scientific Data* 3:160018. DOI
  [10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18).
- Wilson, G., Bryan, J., Cranston, K., Kitzes, J., Nederbragt, L., Teal,
  T. K. 2017. Good Enough Practices in Scientific Computing. *PLOS
  Computational Biology* 13(6):e1005510. DOI
  [10.1371/journal.pcbi.1005510](https://doi.org/10.1371/journal.pcbi.1005510).
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. 2023. Judging LLM-as-a-Judge
  with MT-Bench and Chatbot Arena. arXiv:2306.05685.
  <https://arxiv.org/abs/2306.05685>.

Software-tool references without primary literature:

- conda-lock. <https://github.com/conda/conda-lock> (accessed 2026-05-18).
- Quarto. <https://quarto.org/> (accessed 2026-05-18).
- renv (Ushey, K., Wickham, H.). CRAN package.
  <https://cran.r-project.org/package=renv>;
  <https://rstudio.github.io/renv/> (accessed 2026-05-18).
