---
name: pre-register-hypothesis
description: Freeze the design document for a hypothesis. Writes design.md from the 11-section template, computes its SHA-256, emits a ReproLog with config_resolved_sha256 = design.md SHA, and commits via commit-with-provenance. After freeze, the design is immutable — any change requires a new HID. Quant-project workflow; for epi protocols see docs/protocol/protocol_v0.md.
---

# pre-register-hypothesis

## When to invoke

After `hypothesis-new H<NNN>` creates a backlog row, before any data analysis on that hypothesis begins. Pre-registration is the freeze point: the design is fixed, all subsequent runs (validation, power analysis, walk-forward, KPI report) must match what was registered.

## Gate position

```
hypothesis-new
    └─► pre-register-hypothesis          ← THIS SKILL
        └─► power-analysis
            └─► validate-data
                └─► statistical-analysis
                    └─► commit-with-provenance + deliver-results
```

Power-analysis runs AFTER pre-registration (you cannot power-test an unspecified hypothesis) and BEFORE validate-data (power informs whether n is adequate; if n is too small, do not proceed).

## Procedure

1. **Verify pre-conditions**
   - Project has `hypothesis_backlog.md` at root with a row matching H<NNN>.
   - `research/01_hypothesis_register/H<NNN>/` exists (created by `hypothesis-new`).
   - The HID is in status `designed` (initial state) — never freeze a hypothesis that was already in `running` or later.

2. **Populate design.md from the template**
   Render `assets/hypothesis_design_TEMPLATE.md` with substitutions:
   - `{HID}` → the hypothesis ID
   - `{TITLE}` → from the backlog row
   - `{TIER}` → from the backlog row
   - `{DATE}` → today's ISO date
   - `{CITATIONS}` → comma-separated DOI list from the backlog `Mechanism citation` cell

   Write to `research/01_hypothesis_register/H<NNN>/design.md`. **Refuse to overwrite** an existing design.md unless `--force` is set and the user provides justification (which gets recorded in the commit body).

3. **Prompt the user (or accept arg-passed values) for the 11 sections.** This is the substantive content fill-in:
   - §1 Hypothesis — H0/H1; mechanism; citations
   - §2 Universe & sample period — instruments, freq, windows
   - §3 Features — feature@version
   - §4 Label construction — triple-barrier params
   - §5 Estimator — model class + hyperparameter grid
   - §6 Splitter — purge + embargo derivation
   - §7 Cost model — reference cost_model_id
   - §8 Gate thresholds — alpha, BH threshold, DSR activation
   - §9 Stopping rule — fixed folds or budget
   - §10 Decision rule — disposition mapping
   - §11 Reproducibility commitments — fields auto-populated at run time

   If the user provides only partial content, leave `<TODO>` markers where unfilled; pre-registration freezes whatever is present, so the user should fill everything before invoking this skill.

4. **Compute design.md SHA-256** (full 64-hex, raw bytes via `hashlib.sha256(path.read_bytes()).hexdigest()`).

5. **Emit ReproLog** with:
   - `phase = "validation"` (pre-registration is a validation/freeze step, not run-time)
   - `hypothesis_id = H<NNN>`
   - `config_resolved_sha256 = <design.md SHA>`
   - All other fields populated by `emit_repro_log.capture()` defaults
   ReproLog file at `logs/reproducibility/repro_log_<run_id>.json`.

6. **Update backlog row** in `hypothesis_backlog.md`:
   - Change `status: designed` to `status: designed` (no change) **and** add the design.md SHA to the row's `Notes` cell as `frozen_sha256=<sha[:12]>`.

7. **Commit** with `--role=prose` (pre-registration is design-doc prose, not code):
   ```
   commit-with-provenance "feat(pre-reg): freeze H<NNN> design.md" --role=prose
   ```

8. **External pre-registration (optional)**: if `--external=osf` flag is passed and OSF MCP is available, upload the design.md to OSF as a private project, capture the OSF DOI, and add it to the design.md `external_doi:` frontmatter field. Default: internal-only (no external posting); design.md SHA in the ReproLog suffices as a tamper-evident freeze record.

## Hand-off

After completion:
- Call `power-analysis H<NNN>` to compute required n for the pre-registered effect of interest.
- `pre-register-hypothesis` writes the freeze-point ReproLog; `power-analysis` will write its own ReproLog when run.

## Identity hygiene

The `owner:` frontmatter field is left blank by default. Populate it with the project owner if your workflow requires authorship attribution on the freeze record; otherwise leave the placeholder. The committed file is signed by whatever `git config user.email` resolves to.

## References

- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. — §3.2 (triple-barrier), §7 (purged CV), §12 (CPCV)
- Foster, E. D., & Deardorff, A. (2017). "Open Science Framework (OSF)." *J Med Libr Assoc* 105(2):203. https://doi.org/10.5195/jmla.2017.88 — external pre-registration target
- AsPredicted: https://aspredicted.org/ — short-form pre-reg alternative
