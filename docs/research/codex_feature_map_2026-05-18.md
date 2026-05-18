# Codex CLI Feature Map and Porting Notes (2026-05-18)

## Provenance

Synthesized from web research on OpenAI Codex CLI customization surfaces
and from an inventory of an existing Claude Code customization layer that
this repository is being adapted from.

Primary sources (OpenAI Codex CLI documentation, accessed 2026-05-18):

- [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [Subagents](https://developers.openai.com/codex/subagents)
- [Skills](https://developers.openai.com/codex/skills)
- [Custom prompts (deprecated)](https://developers.openai.com/codex/custom-prompts)
- [Hooks](https://developers.openai.com/codex/hooks)
- [Slash commands](https://developers.openai.com/codex/cli/slash-commands)
- [MCP](https://developers.openai.com/codex/mcp)
- [Config reference](https://developers.openai.com/codex/config-reference)
- [Advanced config](https://developers.openai.com/codex/config-advanced)
- [Agent approvals and security](https://developers.openai.com/codex/agent-approvals-security)
- [CLI install](https://developers.openai.com/codex/cli)
- [openai/codex on GitHub](https://github.com/openai/codex)

## Codex CLI install and configuration

- Install: `npm i -g @openai/codex`, `brew install --cask codex`, or
  GitHub release binary.
- Authentication: ChatGPT login or `OPENAI_API_KEY` environment variable.
- Config home: `~/.codex/` (override via `CODEX_HOME` environment
  variable).
- Project scope: `<repo>/.codex/` (honored only when explicitly trusted).
- CLI and the official IDE extension share `~/.codex/config.toml`.

## Surface-by-surface mapping

| Source-system surface | Codex equivalent? | Codex path / file | Schema notes |
|---|---|---|---|
| Hierarchical project + user instructions | Yes | `~/.codex/AGENTS.md` (global) + `<repo>/AGENTS.md` + per-subfolder `AGENTS.md` walked from git root to current working directory | Plain markdown. Concatenated root-to-leaf (leaf overrides). `AGENTS.override.md` honored first. Hard cap 32 KiB total (`project_doc_max_bytes` tunable). Fallback names allowed via `project_doc_fallback_filenames` in `config.toml`. |
| Subagents (markdown frontmatter in source system) | Yes | `~/.codex/agents/<name>.toml` (user) or `<repo>/.codex/agents/<name>.toml` (project) | TOML, not markdown. Required: `name`, `description`, `developer_instructions`. Optional: `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`, `nickname_candidates`. Spawned only on explicit request. Caps in `[agents]`: `max_threads = 6`, `max_depth = 1`. |
| Skills (directory with `SKILL.md`) | Yes | `~/.codex/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md` (user); `<repo>/.agents/skills/` (project); `/etc/codex/skills/` (admin) | Skill is a directory, not a single file. Required `SKILL.md` with frontmatter `name` + `description`; optional `scripts/`, `references/`, `assets/`, `agents/openai.yaml`. Progressive disclosure: description visible first, body loaded on selection. Invoked via `/skills`, `$skillname`, or implicit auto-matching on description. |
| Slash commands (markdown files) | Partial; deprecated path | `~/.codex/prompts/*.md` (deprecated; migrate to skills) | YAML frontmatter `description`, `argument-hint`. Placeholders: `$1..$9`, `$ARGUMENTS`, `$NAMED_KEY` (passed as `KEY=value`), `$$`. Invoke as `/prompts:name`. OpenAI now recommends skills for this use case. |
| Lifecycle hooks | Yes (stable) | `~/.codex/hooks.json` or inline `[hooks]` in `config.toml`; project `<repo>/.codex/hooks.json`; plugin-bundled; enterprise `requirements.toml` | Events: SessionStart, PreToolUse, PermissionRequest, PostToolUse, UserPromptSubmit, Stop. Schema: `Event → matcher (regex) → hooks[]` with `type: "command"`, `command`, `timeout` (default 600 seconds), `statusMessage`. Hooks receive JSON stdin (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `permission_mode`) and respond with JSON (`continue`, `stopReason`, `systemMessage`). **No SessionEnd event** — `Stop` is the closest. |
| Settings (permissions, environment, statusline, model) | Yes (different schema, TOML) | `~/.codex/config.toml` (user), `<repo>/.codex/config.toml` (project, trusted only) | TOML. Holds model, sandbox/approval policy, `[mcp_servers]`, `[hooks]`, `[agents]`, `[tui.keymap]`, `project_doc_max_bytes`, `project_doc_fallback_filenames`. |
| Keybindings | Yes | `[tui.keymap]` block in `config.toml`; manage via `/keymap` slash command | Key names: `ctrl-a`, `shift-enter`, `page-down`, etc. Context-specific overrides; empty list unbinds. `/vim` modal editing has a separate keymap context. |
| MCP server declarations | Yes | `[mcp_servers.<name>]` tables in `~/.codex/config.toml` (or project `.codex/config.toml`); manage via `codex mcp` CLI | Supports stdio (`command` + `--env KEY=VALUE`) and streamable HTTP URLs. Shared between Codex CLI and IDE extension. |
| Auto-managed persistent memory | No equivalent | — | Codex relies on AGENTS.md (manually maintained) and skills' progressive disclosure. Auto-write memory feature does not survive the port. |

## High-friction porting items

1. **Session-end audit-trail hook → `Stop` event.** `Stop` fires per turn,
   not per session. A naive port emits the audit trail every turn
   (wasteful) or never (broken). Likely mitigation: emit once per turn
   into a rolling file and let an external job aggregate, or maintain an
   in-process debounce flag that flushes when no further turns arrive
   within a window.

2. **`@import` directives in the source-system root instruction file.**
   AGENTS.md does not support `@import` syntax. Two routings exist:
   (a) inline the imported rules files into the top-level AGENTS.md;
   (b) place each rules file as a per-subdirectory `AGENTS.md` so the
   git-root → cwd walk activates them by path. Option (b) maps more
   cleanly onto cwd-prefix glob activation than the import did.

3. **Subagents are TOML, not markdown frontmatter.** Each subagent
   definition needs a format conversion (`description`, `tools` →
   `description`, `developer_instructions`, optional `mcp_servers`,
   `sandbox_mode`).

4. **Slash commands route to skills, not deprecated `prompts/`.** Porting
   to skills means restructuring each command body into a `SKILL.md` with
   progressive-disclosure body. More work than the deprecated path, but
   forward-compatible.

5. **No auto-managed memory equivalent.** Either accept the loss or
   maintain manually in AGENTS.md.

6. **Deployer needs a Codex target.** Idempotent backup + deploy pattern
   from the source-system installer can be reused wholesale; targets and
   schema (TOML vs. JSON) differ.

## Plugin distribution

Codex CLI has an official plugin marketplace:
`codex plugin marketplace add <source>` accepts `owner/repo[@ref]` GitHub
shorthand, HTTP(S) Git URLs, SSH Git URLs, and local directories. Plugins
can bundle hooks (gated by `plugin_hooks = true`).

No community-curated "awesome-codex" dotfile aggregator surfaced in
research; sharing happens via the plugin marketplace mechanism rather
than dotfile aggregators.

## Open question to resolve before implementation

Whether to (a) keep skill `SKILL.md` files identical so the same files
deploy to both Claude Code and Codex CLI, or (b) maintain two separate
skill trees. Option (a) is cheaper if skill bodies do not depend on
Claude-specific tool names; option (b) is necessary if they do. A
targeted audit of the source skill files settles this and should run
before any large-scale porting.
