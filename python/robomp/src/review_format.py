"""Reconcile the verdict counts in a PR review summary with the staged findings.

The model writes the review summary in Chinese. Left alone, its own tally of
findings drifts from the actual list, so a verdict can claim two should-fix
items while listing three. This module rewrites only the count clause inside
the 结论 heading, keeping the model's verdict, rank, and prose. Staged inline
comments carry the severity prefixes the kickoff prompt prescribes, so they
are the authority for the tallies.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Severity prefixes shared with the review kickoff prompt. A staged comment
# without a recognised prefix is counted as should-fix rather than dropped:
# silently losing a finding from the tally is worse than misclassifying it.
_SEVERITIES: tuple[tuple[str, str], ...] = (("阻塞项", "阻塞"), ("应改项", "应改"), ("建议", "建议"))
_DEFAULT_SEVERITY = "应改"

# A count clause is "N 条 <label>" optionally written with Arabic or Chinese
# digits, separated from the next clause by any of the usual separators. The
# label after the count is enough to anchor the match; no look-behind is needed,
# and one would wrongly fire on the Chinese text preceding the digit.
_COUNT_RE = re.compile(r"\d+\s*条\s*(阻塞|应改|建议)")

_CHINESE_DIGITS = "零一二三四五六七八九十"


def severity_of(body: str) -> str:
    """Classify one inline comment body by its leading severity prefix."""
    head = body.lstrip()[:8]
    for prefix, label in _SEVERITIES:
        if head.startswith(prefix):
            return label
    return _DEFAULT_SEVERITY


def count_severities(bodies: Iterable[str]) -> dict[str, int]:
    """Tally findings per severity label, in kickoff-prompt order."""
    counts = {label: 0 for _, label in _SEVERITIES}
    for body in bodies:
        counts[severity_of(body)] += 1
    return counts


def format_counts(counts: dict[str, int]) -> str:
    """Render "1 条阻塞、2 条应改" for the verdict clause; empty when no findings."""
    return "、".join(f"{counts[label]} 条{label}" for _, label in _SEVERITIES if counts.get(label))


def reconcile_verdict_counts(body: str, bodies: Iterable[str]) -> str:
    """Replace the count clause of the 结论 heading with the staged tallies.

    Only the clause that carries a count is touched. When the model already
    agrees, or when the 结论 heading is absent, the text is returned unchanged.
    """
    counts = count_severities(bodies)
    rendered = format_counts(counts)
    match = re.search(r"^##\s*结论\s*$", body, re.MULTILINE)
    if match is None:
        return body
    # The heading's own newline ends the heading line, so the verdict sentence
    # starts after it and runs to the next line break.
    start = match.end() + 1
    if start > len(body):
        return body
    end = body.find("\n", start)
    if end == -1:
        end = len(body)
    verdict = body[start:end]
    if not _COUNT_RE.search(verdict):
        return body
    if verdict.count("评级") == 0 and "P" not in verdict:
        # No rank on this line: it is likely a stray clause, leave it alone.
        return body
    # Rebuild: strip every "N 条 <label>" occurrence and the separators they
    # leave behind, then splice the authoritative clause back after the rank.
    cleaned = _COUNT_RE.sub("", verdict)
    # Removing a clause can leave doubled or dangling separators. Collapse
    # them and drop any that end up next to the sentence-ending full stop.
    cleaned = re.sub(r"[，,、;；]{2,}", "，", cleaned)
    cleaned = re.sub(r"[，,、;；]+(?=\s*[。！？!?])", "", cleaned)
    cleaned = re.sub(r"^[，,、;；\s]+", "", cleaned)
    cleaned = re.sub(r"[，,、;；\s]+$", "", cleaned)
    rank_match = re.search(r"评级\s*P[0-3]", cleaned)
    if rank_match is None:
        return body
    head = cleaned[: rank_match.end()].strip()
    tail = cleaned[rank_match.end() :].strip()
    tail = re.sub(r"^[，,、;；\s]+", "", tail)
    parts = [head]
    if rendered:
        parts.append(rendered)
    if tail:
        parts.append(tail)
    # A tail that opens with sentence punctuation must not be preceded by a
    # separator, otherwise we would write "评级 P1，。".
    rebuilt = parts[0]
    for part in parts[1:]:
        if part[0] in "。！？!?":
            rebuilt += part
        else:
            rebuilt += "，" + part
    return body[:start] + rebuilt + body[end:]


def strip_ai_footer(body: str) -> str:
    """Remove a trailing generated-by-AI line if the model adds one anyway.

    Only a standalone footer line qualifies; a mid-sentence mention inside the
    review prose is left alone.
    """
    text = body.rstrip()
    # The footer is its own line and starts with the marker. A mid-sentence
    # mention inside review prose is not a footer and stays untouched.
    pattern = re.compile(r"\n{1,2}\s*generated\s+by\s+AI[^\n]*$", re.IGNORECASE)
    stripped = pattern.sub("", text).rstrip()
    if stripped == text:
        stripped = re.sub(r"^\s*generated\s+by\s+AI[^\n]*$", "", text, flags=re.IGNORECASE).rstrip()
    return stripped


__all__ = [
    "count_severities",
    "format_counts",
    "reconcile_verdict_counts",
    "severity_of",
    "strip_ai_footer",
]
