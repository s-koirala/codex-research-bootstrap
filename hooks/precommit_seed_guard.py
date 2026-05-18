#!/usr/bin/env python3
"""Pre-commit-framework hook: seed / magic-number guard.

Reads staged file paths from argv. Fails with exit 1 on any violation so
pre-commit blocks the commit.

Detection is AST-driven when parseable (seed/RNG matches inside strings and
comments are ignored). Function scopes are precomputed once per file;
enclosing-func lookup is O(log F) via bisect. sklearn estimators called
without an explicit random_state kwarg are flagged via AST keyword
inspection. Falls back to whole-file regex on SyntaxError.

Usage (via .pre-commit-config.yaml) - Windows-safe invocation:
    - id: seed-guard
      name: seed and magic-number guard
      entry: python
      args: [hooks/precommit_seed_guard.py]
      language: system
      files: \\.(py|ipynb)$
      pass_filenames: true

Python 3.10+ stdlib only.
"""
from __future__ import annotations

import ast
import bisect
import json
import re
import sys
from pathlib import Path

SEED_PATTERNS_RE = [
    re.compile(r"\bnp\.random\.(?!seed|default_rng|RandomState|SeedSequence|Generator)\w+\s*\("),
    re.compile(r"\btorch\.(rand|randn|randint|randperm|bernoulli|multinomial)\s*\("),
    re.compile(r"(?<!\.)\brandom\.(?!seed|Random|SystemRandom)\w+\s*\("),
]
SEED_DECLARED_RE = re.compile(
    r"(np\.random\.seed|default_rng|torch\.manual_seed|random\.seed|"
    r"random_state\s*=\s*\d+|seed\s*=\s*\d+|SeedSequence)"
)
MAGIC_KEYS = re.compile(
    r"\b(threshold|learning_rate|lr|n_boot|n_iter|n_trials|"
    r"confidence|min_samples|max_depth|n_estimators|lambda_|gamma|penalty)\s*=\s*"
    r"([0-9]+\.?[0-9]*(?:e-?\d+)?)"
)
JUSTIFY = re.compile(r"#\s*(justify|cv|bayes|grid|bootstrap|lit|ref):")
SKIP_TOKEN = re.compile(r"\b(test|assert)\b|#\s*noqa")

JUSTIFY_LOOKBACK_LINES = 3
MAX_REPORTED_ISSUES = 3
MAX_SNIPPET_CHARS = 80

_NP_UNSAFE = {"rand", "randn", "randint", "random", "ranf", "sample", "choice",
              "normal", "uniform", "poisson", "binomial", "exponential",
              "beta", "gamma", "chisquare", "bytes", "permutation", "shuffle"}
_TORCH_UNSAFE = {"rand", "randn", "randint", "randperm", "bernoulli", "multinomial"}
_RANDOM_SAFE = {"seed", "Random", "SystemRandom"}
_SKLEARN_PREFIX = "sklearn"


def is_excluded(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if {"tests", "test", "fixtures"} & parts:
        return True
    name = path.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".ipynb":
        try:
            nb = json.loads(path.read_text(encoding="utf-8"))
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
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _attr_chain(node: ast.AST) -> str:
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


def _literal_int(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return True
    return isinstance(node, ast.Name)


def _is_seed_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _attr_chain(node.func)
    if name in ("np.random.seed", "numpy.random.seed", "torch.manual_seed", "random.seed"):
        return True
    tail = name.rsplit(".", 1)[-1] if name else ""
    return tail in ("default_rng", "SeedSequence")


def _is_seed_kwarg(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    for kw in node.keywords:
        if kw.arg in ("seed", "random_state") and _literal_int(kw.value):
            return True
    return False


def _unsafe_rng_calls(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        if not chain:
            continue
        parts = chain.split(".")
        tail = parts[-1]
        if len(parts) >= 3 and parts[0] in ("np", "numpy") and parts[1] == "random":
            if tail in _NP_UNSAFE:
                out.append((node.lineno, f"{chain}("))
        elif len(parts) == 2 and parts[0] == "torch" and tail in _TORCH_UNSAFE:
            out.append((node.lineno, f"{chain}("))
        elif len(parts) == 2 and parts[0] == "random" and tail not in _RANDOM_SAFE:
            out.append((node.lineno, f"{chain}("))
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


def _sklearn_unset_random_state(tree: ast.AST, aliases: set[str]) -> list[tuple[int, str]]:
    if not aliases:
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        chain = _attr_chain(node.func)
        top = chain.split(".", 1)[0] if chain else ""
        if top not in aliases:
            continue
        kws = {kw.arg for kw in node.keywords if kw.arg}
        if "random_state" not in kws:
            out.append((node.lineno, f"{chain}(<no random_state>)"))
            continue
        for kw in node.keywords:
            if kw.arg == "random_state" and isinstance(kw.value, ast.Constant) and kw.value.value is None:
                out.append((node.lineno, f"{chain}(random_state=None)"))
    return out


def _seed_linenos(tree: ast.AST) -> list[int]:
    return sorted({node.lineno for node in ast.walk(tree)
                   if _is_seed_call(node) or _is_seed_kwarg(node)})


class _Scopes:
    def __init__(self, tree: ast.AST) -> None:
        spans: list[tuple[int, int, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", None) or node.lineno
                spans.append((node.lineno, end, id(node)))
        spans.sort()
        self._starts = [s[0] for s in spans]
        self._spans = spans

    def enclosing_id(self, lineno: int) -> int | None:
        idx = bisect.bisect_right(self._starts, lineno) - 1
        while idx >= 0:
            s, e, nid = self._spans[idx]
            if s <= lineno <= e:
                return nid
            if e < lineno:
                break
            idx -= 1
        return None


def _truncate(s: str, n: int = MAX_SNIPPET_CHARS) -> str:
    return s if len(s) <= n else s[: n - 1] + "..."


def scan(path: Path) -> list[str]:
    text = read_text(path)
    if not text.strip():
        return []
    issues: list[str] = []

    try:
        tree = ast.parse(text)
        scopes = _Scopes(tree)
        seeds = _seed_linenos(tree)
        unsafe = _unsafe_rng_calls(tree)
        sk_miss = _sklearn_unset_random_state(tree, _sklearn_aliases(tree))

        def seeded(rng_lineno: int) -> bool:
            rng_scope = scopes.enclosing_id(rng_lineno)
            for s in seeds:
                seed_scope = scopes.enclosing_id(s)
                if seed_scope is None and s <= rng_lineno:
                    return True
                if rng_scope is not None and seed_scope == rng_scope:
                    return True
            return False

        for lineno, snip in unsafe:
            if not seeded(lineno):
                issues.append(f"L{lineno}: unseeded RNG `{_truncate(snip)}`")
                if len(issues) >= MAX_REPORTED_ISSUES:
                    break
        for lineno, snip in sk_miss:
            issues.append(f"L{lineno}: sklearn `{_truncate(snip)}` - add explicit random_state")
            if len(issues) >= 2 * MAX_REPORTED_ISSUES:
                break
    except SyntaxError:
        # Regex fallback for partial/invalid code.
        any_seed = bool(SEED_DECLARED_RE.search(text))
        if not any_seed:
            for idx, line in enumerate(text.splitlines(), 1):
                for pat in SEED_PATTERNS_RE:
                    for m in pat.finditer(line):
                        issues.append(f"L{idx}: unseeded RNG `{_truncate(m.group(0))}`")
                        if len(issues) >= MAX_REPORTED_ISSUES:
                            break
                    if len(issues) >= MAX_REPORTED_ISSUES:
                        break
                if len(issues) >= MAX_REPORTED_ISSUES:
                    break

    lines = text.splitlines()
    magic_count = 0
    for i, line in enumerate(lines):
        if SKIP_TOKEN.search(line):
            continue
        for m in MAGIC_KEYS.finditer(line):
            ctx = lines[max(0, i - JUSTIFY_LOOKBACK_LINES) : i + 1]
            if not any(JUSTIFY.search(cl) for cl in ctx):
                issues.append(f"L{i + 1}: magic `{_truncate(m.group(0))}` (add # justify: / # cv: / # ref:)")
                magic_count += 1
                if magic_count >= MAX_REPORTED_ISSUES:
                    return issues
    return issues


def main(argv: list[str]) -> int:
    any_fail = False
    for arg in argv[1:]:
        p = Path(arg)
        if not p.exists() or is_excluded(p):
            continue
        issues = scan(p)
        if issues:
            any_fail = True
            print(f"{p}:", file=sys.stderr)
            for msg in issues:
                print(f"  - {msg}", file=sys.stderr)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
