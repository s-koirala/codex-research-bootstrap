#!/usr/bin/env python3
"""PreToolUse (Write|Edit|MultiEdit|NotebookEdit) hook: flag un-seeded RNG calls
and unjustified magic numbers in Python / notebook writes.

Reproducibility context: arXiv 2512.22387 (68.3% reproducibility rate for LLM-
generated code; Python subset 89.2%). Bootstrap policy mandates explicit seeds
and empirical parameter justification (see AGENTS.md "Parameter & Prompt
Selection").

Detection is AST-driven when parseable. Seed / RNG / sklearn-random_state hits
inside strings, comments, or docstrings are ignored. Function scopes are
precomputed once per file; enclosing-func lookup is O(log F) via bisect.
sklearn estimators called without an explicit `random_state=<value>` kwarg are
flagged via AST keyword inspection. Falls back to whole-file regex on
SyntaxError so partial edits still pass.

Emits permissionDecision=ask (not deny). Fails open on any exception.
Python 3.10+ stdlib only.
"""
from __future__ import annotations

import ast
import bisect
import json
import re
import sys
from pathlib import Path

# Regex-only fallback (used when ast.parse fails - partial edits).
SEED_PATTERNS_RE = [
    re.compile(r"\bnp\.random\.(?!seed|default_rng|RandomState|SeedSequence|Generator)\w+\s*\("),
    re.compile(r"\btorch\.(rand|randn|randint|randperm|bernoulli|multinomial)\s*\("),
    re.compile(r"(?<!\.)\brandom\.(?!seed|Random|SystemRandom)\w+\s*\("),
]
SEED_DECLARED_RE = re.compile(
    r"(np\.random\.seed|default_rng|torch\.manual_seed|random\.seed|"
    r"random_state\s*=\s*\d+|seed\s*=\s*\d+|SeedSequence)"
)

# `alpha` omitted - matplotlib/seaborn kwarg collision.
# `tol`/`eps`/`epsilon` omitted - convergence criteria, not hyperparameters
# of inferential interest; flagging caused ask-fatigue.
MAGIC_KEYS = re.compile(
    r"\b(threshold|learning_rate|lr|n_boot|n_iter|n_trials|"
    r"confidence|min_samples|max_depth|n_estimators|lambda_|gamma|penalty)\s*=\s*"
    r"([0-9]+\.?[0-9]*(?:e-?\d+)?)"
)
JUSTIFY = re.compile(r"#\s*(justify|cv|bayes|grid|bootstrap|lit|ref):")
SKIP_TOKEN = re.compile(r"\b(test|assert)\b|#\s*noqa")

MULTI_FIELD_KEYS = ("content", "new_string", "new_source")

# Block-comment idiom tolerance (NumPy/SciPy convention: 1-3 line blocks).
JUSTIFY_LOOKBACK_LINES = 3
# Truncation budgets for permission-ask reason (keep reason scannable).
MAX_REPORTED_ISSUES = 3
MAX_SNIPPET_CHARS = 80
MAX_REASON_CHARS = 1000

# Unseeded-RNG call signatures by top-level-qualifier.
_NP_UNSAFE = {"rand", "randn", "randint", "random", "ranf", "sample", "choice",
              "normal", "uniform", "poisson", "binomial", "exponential",
              "beta", "gamma", "chisquare", "bytes", "permutation", "shuffle"}
_TORCH_UNSAFE = {"rand", "randn", "randint", "randperm", "bernoulli", "multinomial"}
_RANDOM_SAFE = {"seed", "Random", "SystemRandom"}

# sklearn estimator name hints - any module path starting with sklearn. whose
# Call lacks an explicit random_state kwarg is flagged.
_SKLEARN_PREFIX = "sklearn"


def _is_seed_call(node: ast.AST) -> bool:
    """np.random.seed(...), torch.manual_seed(...), random.seed(...),
    default_rng(...), SeedSequence(...)."""
    if not isinstance(node, ast.Call):
        return False
    name = _attr_chain(node.func)
    if name in ("np.random.seed", "numpy.random.seed", "torch.manual_seed",
                "random.seed"):
        return True
    tail = name.rsplit(".", 1)[-1] if name else ""
    return tail in ("default_rng", "SeedSequence")


def _is_seed_kwarg(node: ast.AST) -> bool:
    """A Call with keyword seed=<literal int>, random_state=<literal int>."""
    if not isinstance(node, ast.Call):
        return False
    for kw in node.keywords:
        if kw.arg in ("seed", "random_state") and _literal_int(kw.value):
            return True
    return False


def _literal_int(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return True
    if isinstance(node, ast.Name):  # seed=SEED where SEED is a module var
        return True
    return False


def _attr_chain(node: ast.AST) -> str:
    """Reduce Attribute/Name chain to dotted string; '' if not resolvable."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    else:
        return ""
    return ".".join(reversed(parts))


def _unsafe_rng_calls(tree: ast.AST) -> list[tuple[int, str]]:
    """Walk tree for RNG calls that need seeding; return (lineno, display)."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        if not chain:
            continue
        parts = chain.split(".")
        tail = parts[-1]
        # np.random.<fn> where fn is unsafe
        if len(parts) >= 3 and parts[0] in ("np", "numpy") and parts[1] == "random":
            if tail in _NP_UNSAFE:
                out.append((node.lineno, f"{chain}("))
        # torch.<fn>
        elif len(parts) == 2 and parts[0] == "torch" and tail in _TORCH_UNSAFE:
            out.append((node.lineno, f"{chain}("))
        # random.<fn> (stdlib)
        elif len(parts) == 2 and parts[0] == "random" and tail not in _RANDOM_SAFE:
            out.append((node.lineno, f"{chain}("))
    return out


def _sklearn_unset_random_state(tree: ast.AST, import_aliases: set[str]) -> list[tuple[int, str]]:
    """Calls to sklearn-imported names lacking an explicit random_state kwarg."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        top = chain.split(".", 1)[0] if chain else ""
        if top not in import_aliases:
            continue
        kws = {kw.arg for kw in node.keywords if kw.arg}
        if "random_state" not in kws:
            continue
        # present but explicit None -> still flag
        flagged = False
        for kw in node.keywords:
            if kw.arg == "random_state":
                if isinstance(kw.value, ast.Constant) and kw.value.value is None:
                    flagged = True
                break
        if flagged:
            out.append((node.lineno, f"{chain}(random_state=None)"))
    # Also: imported estimator call with NO random_state kwarg at all.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        top = chain.split(".", 1)[0] if chain else ""
        if top not in import_aliases:
            continue
        kws = {kw.arg for kw in node.keywords if kw.arg}
        if "random_state" not in kws:
            out.append((node.lineno, f"{chain}(<no random_state>)"))
    return out


def _sklearn_aliases(tree: ast.AST) -> set[str]:
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(_SKLEARN_PREFIX):
            for n in node.names:
                aliases.add(n.asname or n.name)
        elif isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith(_SKLEARN_PREFIX):
                    aliases.add(n.asname or n.name.split(".")[0])
    return aliases


def _seed_linenos(tree: ast.AST) -> list[int]:
    """Lines where a real seed call / kwarg occurs (AST-filtered, so no
    matches inside strings/comments)."""
    lines: list[int] = []
    for node in ast.walk(tree):
        if _is_seed_call(node) or _is_seed_kwarg(node):
            lines.append(node.lineno)
    return sorted(set(lines))


class _Scopes:
    """Precomputed function spans; O(log F) enclosing-func lookup."""

    def __init__(self, tree: ast.AST) -> None:
        spans: list[tuple[int, int, int]] = []  # (start, end, id)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", None) or node.lineno
                spans.append((node.lineno, end, id(node)))
        spans.sort()
        self._starts = [s[0] for s in spans]
        self._spans = spans

    def enclosing_id(self, lineno: int) -> int | None:
        # Find the innermost span containing lineno.
        idx = bisect.bisect_right(self._starts, lineno) - 1
        best: int | None = None
        while idx >= 0:
            s, e, nid = self._spans[idx]
            if s <= lineno <= e:
                return nid
            if e < lineno:
                break
            idx -= 1
        return best


def gather_text(tool_input: dict) -> str:
    parts: list[str] = []
    for k in MULTI_FIELD_KEYS:
        v = tool_input.get(k)
        if isinstance(v, str):
            parts.append(v)
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for e in edits:
            if isinstance(e, dict):
                for k in MULTI_FIELD_KEYS:
                    v = e.get(k)
                    if isinstance(v, str):
                        parts.append(v)
    return "\n".join(parts)


def read_existing(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return ""
        if p.suffix.lower() == ".ipynb":
            return _ipynb_code_source(p.read_text(encoding="utf-8"))
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _ipynb_code_source(raw: str) -> str:
    """Concatenate only code cells, separated by a blank line so scopes don't
    fuse across cells."""
    try:
        nb = json.loads(raw)
    except Exception:
        return ""
    cells = nb.get("cells", []) if isinstance(nb, dict) else []
    out: list[str] = []
    for c in cells:
        if not isinstance(c, dict) or c.get("cell_type") != "code":
            continue
        src = c.get("source", "")
        out.append("".join(src) if isinstance(src, list) else str(src))
    return "\n\n".join(out)


def _analyse(text: str) -> dict:
    """Returns {'parse_ok': bool, 'unseeded': [(lineno, snippet), ...],
    'seeds': [lineno, ...], 'scopes': _Scopes or None,
    'sklearn_miss': [(lineno, snippet), ...]}.
    Falls back to regex scan for unseeded when parse fails."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        unseeded: list[tuple[int, str]] = []
        for idx, line in enumerate(text.splitlines(), 1):
            for pat in SEED_PATTERNS_RE:
                for m in pat.finditer(line):
                    unseeded.append((idx, m.group(0)))
        return {
            "parse_ok": False,
            "unseeded": unseeded,
            "seeds_any": bool(SEED_DECLARED_RE.search(text)),
            "scopes": None,
            "sklearn_miss": [],
        }
    scopes = _Scopes(tree)
    return {
        "parse_ok": True,
        "unseeded": _unsafe_rng_calls(tree),
        "seeds": _seed_linenos(tree),
        "scopes": scopes,
        "sklearn_miss": _sklearn_unset_random_state(tree, _sklearn_aliases(tree)),
    }


def _is_seeded(info: dict, rng_lineno: int) -> bool:
    if info["parse_ok"]:
        scopes: _Scopes = info["scopes"]
        rng_scope = scopes.enclosing_id(rng_lineno)
        for s in info["seeds"]:
            seed_scope = scopes.enclosing_id(s)
            if seed_scope is None and s <= rng_lineno:
                return True
            if rng_scope is not None and seed_scope == rng_scope:
                return True
        return False
    # Regex fallback: any seed declaration anywhere passes (best-effort).
    return info["seeds_any"]


def _truncate(s: str, n: int = MAX_SNIPPET_CHARS) -> str:
    return s if len(s) <= n else s[: n - 1] + "..."


def emit(decision: str, reason: str) -> None:
    if len(reason) > MAX_REASON_CHARS:
        reason = reason[: MAX_REASON_CHARS - 1] + "..."
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def _is_excluded(p: Path) -> bool:
    parts = {seg.lower() for seg in p.parts}
    if {"tests", "test", "fixtures"} & parts:
        return True
    name = p.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        print(f"pre_write_seed_guard: stdin parse error: {e}", file=sys.stderr)
        return 0

    ti = payload.get("tool_input") or {}
    raw_path = str(ti.get("file_path") or ti.get("notebook_path") or "")
    if not raw_path:
        return 0
    low = raw_path.lower()
    if not (low.endswith(".py") or low.endswith(".ipynb")):
        return 0
    p = Path(raw_path)
    if _is_excluded(p):
        return 0

    new_text = gather_text(ti)
    if not new_text.strip():
        return 0

    existing = read_existing(raw_path)

    # Module-level seed precheck on existing content (pass if the existing
    # file's module scope has a seed before any RNG call). This accepts the
    # Edit/MultiEdit fragment limitation: scope-precise tracking through a
    # patch fragment is ambiguous; we fall back to presence-in-existing.
    existing_info = _analyse(existing) if existing.strip() else None
    existing_module_seed = False
    if existing_info is not None:
        if existing_info["parse_ok"]:
            scopes: _Scopes = existing_info["scopes"]
            for s in existing_info["seeds"]:
                if scopes.enclosing_id(s) is None:
                    existing_module_seed = True
                    break
        else:
            existing_module_seed = existing_info["seeds_any"]

    new_info = _analyse(new_text)

    unseeded_reports: list[str] = []
    if not existing_module_seed:
        for lineno, snippet in new_info["unseeded"]:
            if not _is_seeded(new_info, lineno):
                unseeded_reports.append(f"L{lineno}: {_truncate(snippet)}")

    sklearn_reports = [
        f"L{ln}: {_truncate(snip)}"
        for ln, snip in new_info.get("sklearn_miss", [])
    ]

    magic_unjustified: list[str] = []
    lines = new_text.splitlines()
    for i, line in enumerate(lines):
        if SKIP_TOKEN.search(line):
            continue
        for m in MAGIC_KEYS.finditer(line):
            ctx = lines[max(0, i - JUSTIFY_LOOKBACK_LINES) : i + 1]
            if not any(JUSTIFY.search(cl) for cl in ctx):
                magic_unjustified.append(f"L{i + 1}: {_truncate(m.group(0))}")

    issues: list[str] = []
    if unseeded_reports:
        issues.append(
            "Unseeded RNG calls (no seed at module level or in call's function "
            f"scope): {unseeded_reports[:MAX_REPORTED_ISSUES]}"
        )
    if sklearn_reports:
        issues.append(
            "sklearn estimator without explicit random_state kwarg: "
            f"{sklearn_reports[:MAX_REPORTED_ISSUES]}"
        )
    if magic_unjustified:
        issues.append(
            "Magic numbers without `# justify:` / `# cv:` / `# ref:` comment: "
            f"{magic_unjustified[:MAX_REPORTED_ISSUES]}"
        )

    if issues:
        emit(
            "ask",
            "Reproducibility / parameter-selection guard:\n- "
            + "\n- ".join(issues)
            + "\nAdd explicit seed and an empirical justification comment, or confirm override.",
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"pre_write_seed_guard: unhandled error: {e}", file=sys.stderr)
        sys.exit(0)
