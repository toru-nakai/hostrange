"""Core expansion logic for host range patterns."""

from __future__ import annotations

import re


def _split_top_level(s: str) -> list[str]:
    """Split by commas that are outside of brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _parse_bracket_expr(expr: str) -> list[str]:
    """Parse the contents of [...] into a list of string values.

    Handles:
    - Single values: "5" → ["5"]
    - Ranges: "1-10" → ["1", ..., "10"]
    - Zero-padded ranges: "01-10" → ["01", ..., "10"]
    - Mixed: "1-3,5,7-9" → ["1","2","3","5","7","8","9"]
    """
    results: list[str] = []
    for token in expr.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_str, _, end_str = token.partition("-")
            start = int(start_str)
            end = int(end_str)
            width = len(start_str)
            step = 1 if start <= end else -1
            results.extend(str(i).zfill(width) for i in range(start, end + step, step))
        else:
            results.append(token)
    return results


def _validate(pattern: str) -> None:
    if pattern.count("[") != pattern.count("]"):
        raise ValueError(f"Unmatched brackets in pattern: {pattern!r}")
    if re.search(r"\[\s*\]", pattern):
        raise ValueError(f"Empty brackets in pattern: {pattern!r}")
    if re.search(r"\[\[|\]\]", pattern):
        raise ValueError(f"Nested brackets in pattern: {pattern!r}")


def _expand_single(pattern: str) -> list[str]:
    """Expand a single pattern (no top-level commas)."""
    _validate(pattern)
    segments: list[tuple[str, list[str]]] = []
    last = 0
    for m in re.finditer(r"\[([^\[\]]+)\]", pattern):
        prefix = pattern[last : m.start()]
        values = _parse_bracket_expr(m.group(1))
        segments.append((prefix, values))
        last = m.end()
    suffix = pattern[last:]

    if not segments:
        return [pattern]

    accumulated = [""]
    for prefix, values in segments:
        accumulated = [acc + prefix + v for acc in accumulated for v in values]

    return [s + suffix for s in accumulated]


def expand(patterns: str | list[str]) -> list[str]:
    """Expand host range patterns into a list of hostnames.

    Args:
        patterns: A pattern string like "n[1-10]" or a list of patterns.

    Returns:
        A list of expanded hostname strings.

    Examples:
        >>> expand("n[1-10]")
        ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9', 'n10']
        >>> expand("c[01-05]")
        ['c01', 'c02', 'c03', 'c04', 'c05']
        >>> expand("n[1-3,5-7]")
        ['n1', 'n2', 'n3', 'n5', 'n6', 'n7']
        >>> expand("n[1-3],c[01-03]")
        ['n1', 'n2', 'n3', 'c01', 'c02', 'c03']
        >>> expand(["n[1-2]", "c[01-02]"])
        ['n1', 'n2', 'c01', 'c02']
    """
    if isinstance(patterns, str):
        patterns = [patterns]
    result: list[str] = []
    for pattern in patterns:
        for top in _split_top_level(pattern):
            result.extend(_expand_single(top.strip()))
    return result
