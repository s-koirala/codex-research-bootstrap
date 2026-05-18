# Survey of OpenAI Codex CLI Bootstrap and Customization Repositories (2026-05-18)

## Provenance

**Purpose.** Inventory the public GitHub ecosystem of Codex CLI customization
artifacts — bootstrap installers, dotfile layouts, skill packs, subagent
collections, plugin marketplaces, and hook frameworks — and extract design
conventions usable by this repository (a research-focused Codex CLI bootstrap
layer). The output augments
[docs/research/codex_feature_map_2026-05-18.md](codex_feature_map_2026-05-18.md);
it does not duplicate that feature map.

**Method.** GitHub keyword + structured search:

| Tool | Query (or endpoint) | Filter / sort |
|---|---|---|
| WebSearch | `site:github.com "AGENTS.md" codex CLI bootstrap dotfiles 2026` | relevance |
| WebSearch | `site:github.com ".codex/config.toml" OpenAI codex skills hooks` | relevance |
| WebSearch | `"OpenAI Codex CLI" customization plugin marketplace AGENTS.md` | relevance |
| WebSearch | `github "codex plugin marketplace add" plugin repo` | relevance |
| WebSearch | `site:github.com "codex skills" SKILL.md frontmatter "name:" "description:"` | relevance |
| WebSearch | `site:github.com codex hooks.json SessionStart UserPromptSubmit hooks` | relevance |
| WebSearch | `awesome-codex-cli OR awesome-codex aggregator list github` | relevance |
| WebSearch | `site:github.com ".codex/agents" toml subagent developer_instructions` | relevance |
| GitHub Search API | `q=codex+cli+skills+plugin+OR+%22AGENTS.md%22&sort=stars` | stars desc, 30 per page |
| GitHub Search API | `q=%22codex+plugin+marketplace%22+OR+%22.codex%2Fhooks.json%22&sort=stars` | stars desc |
| GitHub Search API | `q=codex+plugin+OR+codex-plugin+OR+codex-skill+in%3Aname&sort=stars` | stars desc |
| WebFetch | individual repo READMEs, AGENTS.md files, official docs | targeted extraction |

**Accessed.** All URLs accessed 2026-05-18. Repository star counts and last-push
dates captured on the same date and recorded inline.

**Evidence tier.** Cited GitHub repositories are tier-4 (vetted technical
forum); official OpenAI Codex CLI documentation under
[developers.openai.com/codex](https://developers.openai.com/codex) is tier-2
(official documentation). The user evidence hierarchy treats peer-reviewed
literature as tier-1; none of the patterns below have peer-reviewed sources, so
the highest-tier evidence here is the OpenAI developer docs themselves.

## Scope and method

**Inclusion criteria.** A repository qualifies when it (a) ships customization
artifacts that a Codex CLI user installs into `~/.codex/` or a project
`.codex/`, or (b) curates / catalogues such artifacts. The official
[openai/codex](https://github.com/openai/codex) repository is treated as
reference for canonical conventions even though it is the CLI itself.

**Exclusion.** Pure browser extensions, IDE plugins not consuming `.codex/`,
non-English-only meta-lists where the structure is not extractable, and
mobile-only Codex clients are out of scope.

**Weighting.** Stars + last-push-in-2026 + presence of `.codex/` artifacts.
Forks and contributor count consulted as secondary signals only.

## Repos surveyed

Stars and push dates as of 2026-05-18. "Skills / Agents / Hooks / Plugin /
Deployer" columns flag the presence (Y) or absence (N) of that artifact class.

| Repo | URL | Stars | Last push | Sk | Ag | Hk | Pl | De | Notes |
|---|---|---:|---|:-:|:-:|:-:|:-:|:-:|---|
| openai/codex | [link](https://github.com/openai/codex) | 83,493 | 2026-05-18 | – | – | – | – | – | Canonical CLI; reference AGENTS.md (~17 KB, 15 sections). |
| Yeachan-Heo/oh-my-codex | [link](https://github.com/Yeachan-Heo/oh-my-codex) | 28,966 | 2026-05-18 | Y | Y | Y | Y | Y | "oh-my-zsh for Codex"; OMX-delimited AGENTS.md mutation; npm-installed CLI orchestrator. |
| openai/skills | [link](https://github.com/openai/skills) | 19,500 | active | Y | – | – | – | – | Official skill catalog; `.system` / `.curated` / `.experimental` tiers. |
| openai/codex-plugin-cc | [link](https://github.com/openai/codex-plugin-cc) | 18,971 | 2026-04-18 | – | – | – | Y | – | Cross-tool: invoke Codex from Claude Code. |
| EveryInc/compound-engineering-plugin | [link](https://github.com/EveryInc/compound-engineering-plugin) | 16,900 | 2026-05-14 | Y | Y | – | Y | – | 37 skills, 51 agents; multi-platform installer. |
| ComposioHQ/awesome-codex-skills | [link](https://github.com/ComposioHQ/awesome-codex-skills) | 10,405 | 2026-05-15 | Y | – | – | – | – | 38+ skills across 5 categories; documents the canonical skill layout. |
| VoltAgent/awesome-codex-subagents | [link](https://github.com/VoltAgent/awesome-codex-subagents) | 4,744 | 2026-03-20 | – | Y | – | – | – | 136+ subagent TOMLs across 10 categories. |
| openai/codex (AGENTS.md doc) | [link](https://github.com/openai/codex/blob/main/docs/agents_md.md) | – | – | – | – | – | – | – | Canonical AGENTS.md walk; defers to dev portal for full spec. |
| regenrek/codex-1up | [link](https://github.com/regenrek/codex-1up) | 430 | 2026-02-19 | Y | – | Y | – | Y | TypeScript installer; idempotent; `--dry-run`; backups under `~/.codex`. |
| hashgraph-online/awesome-codex-plugins | [link](https://github.com/hashgraph-online/awesome-codex-plugins) | 233 | 2026-05+ | – | – | – | Y | – | Plugin directory; documents `.codex-plugin/plugin.json` schema. |
| RoggeOhta/awesome-codex-cli | [link](https://github.com/RoggeOhta/awesome-codex-cli) | 191 | active | – | – | – | – | – | Cross-category aggregator (~280 entries, ~23 categories as of 2026-05-18; 150/20 at March 2026 announcement). |
| cathrynlavery/codex-skill | [link](https://github.com/cathrynlavery/codex-skill) | 170 | 2026 | Y | – | Y | – | – | Reference skill; ships a `hooks/plan-review.sh`. |
| affaan-m/everything-claude-code | [link](https://github.com/affaan-m/everything-claude-code) | ~186,000* | 2026-04+ | Y | Y | – | – | Y | Separate `.codex/`, `.claude/`, `.cursor/`, `.opencode/`, `.zed/` trees; `install.sh` + `install.ps1`; profile flags. |
| AnswerDotAI/codex-plugins | [link](https://github.com/AnswerDotAI/codex-plugins) | 1 | 2026 | Y | – | – | Y | – | Vendor plugin marketplace; skills namespaced `plugin:skill`. |
| jessfraz/dotfiles (.codex/AGENTS.md) | [link](https://github.com/jessfraz/dotfiles/blob/main/.codex/AGENTS.md) | n/a | 2026 | – | – | – | – | – | Single-author Codex profile; ~16 KB / 10 sections. |
| timoclsn/dotfiles | [link](https://github.com/timoclsn/dotfiles/blob/main/AGENTS.md) | n/a | 2026 | – | – | – | – | – | Symlink pattern: one `AGENTS.md` → `~/.codex/AGENTS.md` + `~/.claude/CLAUDE.md` + opencode. |
| davidgasquez/dotfiles | [link](https://github.com/davidgasquez/dotfiles/blob/main/AGENTS.md) | n/a | 2026 | – | – | – | – | – | Ultra-short single-root AGENTS.md (~877 B). |
| zazencodes/dotfiles `year/2026` | [link](https://github.com/zazencodes/dotfiles/blob/year/2026/AGENTS.md) | n/a | 2026 | – | – | – | – | Y | Symlink + `symlink_dotfiles.sh` helper. |
| danylomikula/dotfiles | [link](https://github.com/danylomikula/dotfiles) | 4 | 2026 | – | – | – | – | Y | Shell `bootstrap.sh` + `configure-ai-agents.sh`; "safe to run multiple times". |
| TonyCasey/ai-dotfiles-manager | [link](https://github.com/TonyCasey/ai-dotfiles-manager) | 1 | 2025-12-17 | – | – | Y | – | Y | Centralizes `.dev/rules/`; copies not symlinks for Windows portability. |
| betterup/codex-cli-subagents | [link](https://github.com/betterup/codex-cli-subagents) | 17 | 2026 | – | Y | – | – | Y | Python `pip install -e .`; markdown-frontmatter agents (not TOML — deviation from docs). |
| shanraisshan/codex-cli-hooks | [link](https://github.com/shanraisshan/codex-cli-hooks) | n/a | 2026 | – | – | Y | – | – | Wires 8 events (adds PreCompact / PostCompact beyond the 6 documented). |

\* The ~186k figure for `everything-claude-code` is the live count from the
GitHub repository header's stars counter as of 2026-05-18 (the project's own
README badge text claims "182K+"; the live header counter is taken as
authoritative). The project is a well-known cross-harness customization
aggregator.

## Pattern findings

### AGENTS.md structure

**Single-root dominates.** Every dotfile-style AGENTS.md inspected
([jessfraz](https://github.com/jessfraz/dotfiles/blob/main/.codex/AGENTS.md),
[davidgasquez](https://github.com/davidgasquez/dotfiles/blob/main/AGENTS.md),
[timoclsn](https://github.com/timoclsn/dotfiles/blob/main/AGENTS.md),
[zazencodes](https://github.com/zazencodes/dotfiles/blob/year/2026/AGENTS.md))
ships one top-level `AGENTS.md`. Per-subdirectory AGENTS.md only appears in
larger codebases. [openai/codex AGENTS.md](https://github.com/openai/codex/blob/main/AGENTS.md)
references one nested style sheet but otherwise keeps prose root-side.

**Length sits well under the 32 KiB cap** (`project_doc_max_bytes` default per
[AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)):

| File | Approx. bytes | % of cap |
|---|---:|---:|
| davidgasquez/dotfiles AGENTS.md | 877 | ~3% |
| timoclsn/dotfiles AGENTS.md | 2,930 | ~9% |
| zazencodes/dotfiles AGENTS.md | 3,950 | ~12% |
| jessfraz/dotfiles .codex/AGENTS.md | 16,100 | ~50% |
| openai/codex AGENTS.md | 17,300 | ~53% |

**No surveyed repo uses AGENTS.override.md.** Discovery order
(`AGENTS.override.md` → `AGENTS.md` → `TEAM_GUIDE.md` → `.agents.md`) is
documented but community use is limited to canonical `AGENTS.md`. Override is
reserved for ad-hoc per-checkout use, not steady-state.

**Override semantics are concatenative.** The chain builds root-down with
closer-to-cwd files appended last, so "files closer to your current directory
override earlier guidance because they appear later in the combined prompt."
`AGENTS.override.md` at a level replaces the regular file at that level only;
global guidance is not eliminated.

**Section convention.** Longer files (openai/codex, jessfraz): identity →
obligations → process → tooling → test philosophy → language-specific blocks
→ handoff/comms. Shorter dotfiles: overview → architecture → patterns → style.

**Mutation-safe AGENTS.md.** [OMX](https://github.com/Yeachan-Heo/oh-my-codex)
wraps its section in `<!-- OMX:AGENTS:START -->` / `<!-- OMX:AGENTS:END -->`
markers and supports `omx setup --merge-agents` to refresh between markers
without trampling hand-written prose. Only delimited-block mutation idiom in
the sample.

### Hook idioms

**Six events officially documented** per
[hooks docs](https://developers.openai.com/codex/hooks): `SessionStart`,
`UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `Stop`.
All but `SessionStart` are turn-scoped. **No `SessionEnd` exists — `Stop`
fires per turn.**

**Some community repos extend the surface.**
[shanraisshan/codex-cli-hooks](https://github.com/shanraisshan/codex-cli-hooks)
documents 8 events including `PreCompact` / `PostCompact`; not in the
published list — treat as unstable.

**SessionEnd absence is unsolved.** OMX, codex-1up, and the surveyed dotfiles
do not document a debounce-or-rollup pattern for once-per-session audit
trails. The [feature map](codex_feature_map_2026-05-18.md) flagged this; the
ecosystem has not converged on a fix.

**Plugin-bundled hooks have a runtime bug.**
[openai/codex#16430](https://github.com/openai/codex/issues/16430) reports
that plugin-local `hooks/hooks.json` files do not execute — the runtime scans
only `~/.codex/hooks.json`. The
[plugin build docs](https://developers.openai.com/codex/plugins/build)
document a `[features].plugin_hooks = true` feature flag that gates
plugin-bundled hooks; the flag defaults off. **For hooks needed today,
install at `~/.codex/hooks.json`.**

**Repo-local hooks misfire in interactive sessions.**
[openai/codex#17532](https://github.com/openai/codex/issues/17532) reports that
hooks configured via a repo-local `.codex/config.toml` do not fire in
interactive sessions — only `~/.codex/hooks.json` and the user-scope
`~/.codex/config.toml` reliably do. **For repository-scoped hooks today,
install at the user scope or via plugin once `[features].plugin_hooks` flips
on by default.**

**Observed payloads.** Hooks shell out to a script reading JSON stdin
(`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`,
`permission_mode`) and printing JSON stdout (`continue`, `stopReason`,
`systemMessage`, `suppressOutput`). Observed use: cost tracking, pre-commit
lint, voice notifications, MCP-server ping, repro-log emission.

### Skill organization

**Canonical layout** (per
[official skills docs](https://developers.openai.com/codex/skills) and the
curated lists). A skill is a directory. Required: `SKILL.md` with YAML
frontmatter `name: <kebab>` + `description: <when-to-fire>`. Optional
siblings: `scripts/` (deterministic helpers Codex shells out to),
`references/` (long-form material, loaded on demand), `assets/` (templates,
icons), `agents/openai.yaml` (UI metadata, invocation policy, tool deps).
[ComposioHQ](https://github.com/ComposioHQ/awesome-codex-skills) explicitly
warns against intra-skill `README.md` / `changelog` — they bloat context.

**Progressive disclosure — three layers.** Codex initially sees only `name` +
`description` (descriptions are capped at ~8,000 chars total across all
installed skills). `SKILL.md` body loads on selection. Scripts and
`references/` load only when the body invokes them. Keep `description`
exhaustive about firing conditions; lean on `references/` for long prose.

**Frontmatter beyond `name` + `description` is not honored.** Optional fields
in surveyed packs (`globs:`, `alwaysApply:`, `version:`, `tags:`) are
Cursor-side, not Codex-side. Avoid them in this bootstrap.

**Discovery and invocation.** Implicit (description match), explicit
`$skill-name`, or interactive `/skills`. Plugin-installed skills prefix as
`pluginname:skillname` ([AnswerDotAI/codex-plugins](https://github.com/AnswerDotAI/codex-plugins)).

### Subagent (.codex/agents/*.toml) idioms

**Spec vs. observed deviates.** Official [subagents docs](https://developers.openai.com/codex/subagents)
require TOML at `.codex/agents/<name>.toml` with `name`, `description`,
`developer_instructions`. Optional: `model`, `model_reasoning_effort`,
`sandbox_mode`, `mcp_servers`, `skills.config`, `nickname_candidates`.

[VoltAgent](https://github.com/VoltAgent/awesome-codex-subagents) ships TOML
but sometimes inlines `developer_instructions` under `[instructions]` with
`text =`. [betterup/codex-cli-subagents](https://github.com/betterup/codex-cli-subagents)
uses markdown+YAML and a Python orchestrator — non-runtime-native. **This
repository should use canonical TOML.**

**Sandbox modes.** `read-only` (auditors, lit-check), `workspace-write`
(remediators), `danger-full-access` (rare, sandbox-isolated only). Per
[agent-approvals-security docs](https://developers.openai.com/codex/agent-approvals-security).
The audit-remediate-loop's five auditors map to `read-only`; only the
remediator step is `workspace-write`.

**MCP wiring.** `mcp_servers = ["name", ...]` selectively exposes a subset of
the user's MCP servers to the spawned thread. Subagent-specific TOML config
(including this filter) is unreliable on Windows per
[openai/codex#19399](https://github.com/openai/codex/issues/19399) — the
Windows runtime spawns named agents with default config rather than honoring
the per-agent TOML. Treat all subagent TOML behavior on Windows as needing
validation.

**Spawn limits.** `[agents].max_threads = 6`, `[agents].max_depth = 1`
defaults. The audit-remediate-loop runs at depth 1 (root spawns five parallel
auditors).

### Deployer design

**Observed installer languages.** TypeScript dominates among heavyweight
installers ([oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) ~94%,
[codex-1up](https://github.com/regenrek/codex-1up) ~95%). Shell dominates
among lightweight personal dotfiles
([danylomikula/dotfiles](https://github.com/danylomikula/dotfiles) ~100%,
zazencodes `symlink_dotfiles.sh`). Cross-platform-shareable installers split
into `install.sh` + `install.ps1` (observed in
[everything-claude-code](https://github.com/affaan-m/everything-claude-code)).
Python `pip install -e .` only for orchestrator-style packages
([betterup/codex-cli-subagents](https://github.com/betterup/codex-cli-subagents)).

**Idempotency conventions.** Two patterns dominate:

1. **State-based skip.** "Idempotent — running it again will skip what's
   already installed" (codex-1up). Implementation: check for file existence
   plus a content hash before overwriting.
2. **Delimited-section mutation.** OMX `<!-- OMX:AGENTS:START -->` markers
   plus `--merge-agents` flag preserve user prose between runs.

**Dry-run support.** Confirmed in
[codex-1up](https://github.com/regenrek/codex-1up) (`--dry-run` previews
changes; uninstall retains backups under `~/.codex`). Most personal dotfiles
do not implement dry-run.

**Scope toggling.** The cleanest pattern is `--target user|project|both` (or
`--scope` equivalent), observed in
[everything-claude-code](https://github.com/affaan-m/everything-claude-code)
via `--target codex|claude|cursor|opencode|zed`. Per-profile bundling
(`--profile minimal|core|full`) lets a single installer ship a dependency-
graded layered install — useful for a research bootstrap where the basic
audit-remediate-loop ships in `minimal`, statistics+epi packs ship in `core`,
and publishing/manuscript pipelines ship in `full`.

**Backup convention.** "Existing configurations are backed up before
modification" (danylomikula/dotfiles) is the common copy. Surveyed
implementations stash backups under `~/.codex/.bootstrap-backups/<timestamp>/`
or equivalent rather than overwriting in place.

**Symlink vs copy.** Dotfile maintainers split. Symlinks
([davidgasquez](https://github.com/davidgasquez/dotfiles/blob/main/AGENTS.md),
[timoclsn](https://github.com/timoclsn/dotfiles/blob/main/AGENTS.md),
[zazencodes](https://github.com/zazencodes/dotfiles)) give a single source of
truth across `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`,
`~/.config/opencode/AGENTS.md`. Copies
([TonyCasey/ai-dotfiles-manager](https://github.com/TonyCasey/ai-dotfiles-manager))
are necessary on Windows without elevated permissions and avoid a known
cross-platform Codex-runtime bug
([openai/codex#15756](https://github.com/openai/codex/issues/15756), with
macOS-filed duplicate
[#17344](https://github.com/openai/codex/issues/17344)) where `SKILL.md`
symlinks under `~/.codex/skills` are skipped by the skills loader (root cause
in `codex-rs/core/src/skills/loader.rs`: file-symlinks are not followed, only
directory-symlinks). **For any cross-platform research bootstrap, prefer
copies for skills and symlinks for AGENTS.md only.**

### Plugin marketplace publishing flow

**Canonical manifest path.** `.codex-plugin/plugin.json` at plugin root, per
[official build docs](https://developers.openai.com/codex/plugins/build).
Required keys: `name` (kebab-case), `version`, `description`. Common optional:
`author`, `homepage`, `repository`, `license`, `keywords`, `skills`,
`mcpServers`, `apps`, `hooks`, `interface`.

**Layout siblings to `.codex-plugin/`.** `skills/` (one subdir per skill),
`hooks/hooks.json` (loaded only when `[features].plugin_hooks = true`), `.app.json`
(app integrations), `.mcp.json` (MCP server declarations), `assets/`.

**Marketplace consumption.** Users run
`codex plugin marketplace add owner/repo[@ref]` (GitHub shorthand),
`codex plugin marketplace add https://…git --sparse path` (sparse checkout for
large marketplaces), or `codex plugin marketplace add ./local-dir` (local
development). The user then browses installed marketplaces in the TUI plugin
view and toggles individual plugins on/off.

**Open runtime bugs to design around.** `plugin_hooks = true` is off by
default; plugin-bundled hooks won't fire until the user opts in. Plan: ship
hooks at both `~/.codex/hooks.json` (works today) **and** `hooks/hooks.json`
inside the plugin (forward-compatible) with installer guidance to flip the
feature flag.

## Gaps and absences

**No community-curated awesome-codex-bootstrap aggregator.** Five "awesome"
lists exist — [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli)
(~280 entries / ~23 categories as of 2026-05-18; 150/20 at March 2026
announcement per [discussion#16329](https://github.com/openai/codex/discussions/16329)),
[milisp/awesome-codex-cli](https://github.com/milisp/awesome-codex-cli),
[KarelDO/awesome-codex](https://github.com/KarelDO/awesome-codex),
[ComposioHQ/awesome-codex-skills](https://github.com/ComposioHQ/awesome-codex-skills),
[VoltAgent/awesome-codex-subagents](https://github.com/VoltAgent/awesome-codex-subagents),
[hashgraph-online/awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) —
but **none aggregates "Codex CLI bootstrap layers" as a category**. RoggeOhta's
list has "Plugins" and "Hooks & Notifications" but no "Deployers" or
"Bootstraps" section. This repository's niche (research-oriented Codex
bootstrap with an audit-remediate-loop) has no direct precedent.

**No conventionalized deployer schema.** Among 5+ installers reviewed, each
invents its own CLI surface (`omx setup`, `codex-1up install`, `install.sh
--target codex`, `ai-dotfiles init`, `bootstrap.sh`). Flag names diverge
(`--dry-run` vs `--preview`, `--force` vs `--replace`, `--merge-agents` vs
`--keep-user`). The dotfiles ecosystem has had stow/chezmoi for a decade;
the Codex-specific ecosystem has not converged.

**No research-domain (stats / epi / public health / manuscript) plugin or
skill pack.** Surveyed plugins span code review, accessibility, security,
SwiftUI, React Native, SEO, KiCAD, even malware analysis — but no
epidemiology / population-health / quant-finance / reporting-standards
collection. The closest neighbors are
[voidful/academic-skills](https://github.com/voidful/academic-skills) and
[Master-cai/Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills),
both small and not domain-specific.

**No documented SessionEnd workaround.** The
[codex_feature_map](codex_feature_map_2026-05-18.md) flagged this; no
community solution has emerged. Bootstraps that need a once-per-session audit
trail (this one does) must implement the debounce themselves.

**Sparse plugin manifests in the wild.** Of the heavyweight plugins inspected
([oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex),
[compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin),
[awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins)),
`plugin.json` is documented in the
[OpenAI plugin build guide](https://developers.openai.com/codex/plugins/build)
but few example manifests are public — most repos ship the artifacts (skills,
agents) without a corresponding `.codex-plugin/plugin.json`, meaning they are
not actually publishable plugins, just clone-and-copy resource bundles. **The
plugin marketplace is younger than the artifacts being published into it.**

## Recommendations for this repository

1. **Single-root AGENTS.md, OMX-style delimited markers.** Wrap the bootstrap-
   managed section in `<!-- AUDIT-LOOP:AGENTS:START -->` / `…END` so installer
   refresh does not trample user-edited prose. Target ~12–15 KB (under the 32
   KiB cap). Inline `rules/quant-project.md`, `rules/population-health.md`,
   `rules/publishing.md` content rather than relying on unsupported `@import`.

2. **Skills as directories from day one.** `SKILL.md` + `scripts/` +
   `references/` + `assets/`. The audit-remediate-loop is a single skill
   referencing auditor subagent definitions from its body. Keep `description`
   exhaustive about firing conditions; do not invent unsupported frontmatter.

3. **Subagents in canonical TOML.** `name` / `description` /
   `developer_instructions` triple, `sandbox_mode = "read-only"` for all five
   auditors, `"workspace-write"` only for the remediator. Wire MCP servers via
   per-agent `mcp_servers = [...]` allowlist; document the Windows caveat.

4. **Dual-path hooks: `~/.codex/hooks.json` + `hooks/hooks.json` in the
   plugin.** User-scope path works today; plugin path is forward-compatible
   when `[features].plugin_hooks = true` flips on by default. SessionStart
   emits the ReproLog envelope (git HEAD, pip freeze SHA-256, dataset
   checksum, RNG seed, model hash).

5. **SessionEnd via Stop+debounce.** Stop hook appends per-turn JSON to
   `logs/turn_<session_id>_<n>.json`; an external job (cron or next-
   SessionStart) aggregates closed sessions and emits the per-session audit
   trail. This is the workaround the [feature map](codex_feature_map_2026-05-18.md)
   flagged and no community solution has emerged.

6. **Cross-platform installer: PowerShell + Bash dual.** Adopt the
   [everything-claude-code](https://github.com/affaan-m/everything-claude-code)
   `install.sh` + `install.ps1` pattern. Flags: `--dry-run`,
   `--scope user|project|both`, `--profile minimal|core|full`, `--backup-dir`,
   `--merge-agents`. Idempotency via content-hash comparison; backups under
   `<scope>/.bootstrap-backups/<timestamp>/`.

7. **Copy skills, symlink AGENTS.md.** Avoid the cross-platform skills-loader
   bug ([openai/codex#15756](https://github.com/openai/codex/issues/15756),
   duplicate [#17344](https://github.com/openai/codex/issues/17344)) where
   symlinked `SKILL.md` files are skipped. AGENTS.md does not exhibit this
   issue.

8. **Ship a publishable `.codex-plugin/plugin.json` from v0.** Marketplace
   consumers add the repo via `codex plugin marketplace add owner/repo`.
   Manifest advertises the audit-remediate-loop skill, reporting-standards
   skills, ReproLog hook, and audit subagents.

9. **Anchor every borrowed convention to its 2026-05-18 source URL.** The
   ecosystem is young enough that conventions shift quarterly; future
   maintainers need traceability to know whether a pattern has since updated.

## References

All accessed 2026-05-18. Tier-2 (official) entries are marked OFFICIAL;
others are tier-4 vetted-technical-forum.

**Official OpenAI Codex CLI documentation (tier-2):**

- [Codex CLI overview](https://developers.openai.com/codex) — OFFICIAL.
- [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md) — OFFICIAL.
- [Skills](https://developers.openai.com/codex/skills) — OFFICIAL.
- [Subagents](https://developers.openai.com/codex/subagents) — OFFICIAL.
- [Hooks](https://developers.openai.com/codex/hooks) — OFFICIAL.
- [Build plugins](https://developers.openai.com/codex/plugins/build) — OFFICIAL.
- [Plugins overview](https://developers.openai.com/codex/plugins) — OFFICIAL.
- [Customization concepts](https://developers.openai.com/codex/concepts/customization) — OFFICIAL.
- [Slash commands](https://developers.openai.com/codex/cli/slash-commands) — OFFICIAL.
- [Agent approvals and security](https://developers.openai.com/codex/agent-approvals-security) — OFFICIAL.

**Open runtime bugs referenced (tier-4, official issue tracker):** issues
14161, 15250, 15266, 15269, 15756, 16012, 16430, 17344, 17532, 18823, 19399,
20210, 21639 in [openai/codex](https://github.com/openai/codex/issues) —
summarized inline above. Community ecosystem size in
[openai/codex discussion#16329](https://github.com/openai/codex/discussions/16329).

**Surveyed repositories (tier-4).** Full URLs and characterizations appear in
the [Repos surveyed](#repos-surveyed) table above. Distinct categories:

- *CLI / reference:* openai/codex, openai/skills, openai/codex-plugin-cc.
- *Workflow layers:* Yeachan-Heo/oh-my-codex, EveryInc/compound-engineering-plugin.
- *Aggregators:* RoggeOhta/awesome-codex-cli, milisp/awesome-codex-cli,
  KarelDO/awesome-codex, ComposioHQ/awesome-codex-skills,
  VoltAgent/awesome-codex-subagents, hashgraph-online/awesome-codex-plugins.
- *Installers:* regenrek/codex-1up, affaan-m/everything-claude-code,
  danylomikula/dotfiles, TonyCasey/ai-dotfiles-manager.
- *Hook / skill exemplars:* shanraisshan/codex-cli-hooks,
  cathrynlavery/codex-skill, AnswerDotAI/codex-plugins.
- *Subagent collections:* VoltAgent/awesome-codex-subagents,
  betterup/codex-cli-subagents.
- *AGENTS.md exemplars:* jessfraz/dotfiles, timoclsn/dotfiles,
  davidgasquez/dotfiles, zazencodes/dotfiles, danielrosehill/Agents.md-Templates.

**Internal references:**

- [docs/SCOPE.md](../SCOPE.md) — mission, audit-remediate-loop, de-identification.
- [docs/decisions/0001-repo-scope-and-naming.md](../decisions/0001-repo-scope-and-naming.md) — context and constraints.
- [docs/research/codex_feature_map_2026-05-18.md](codex_feature_map_2026-05-18.md) — feature map this survey augments.
