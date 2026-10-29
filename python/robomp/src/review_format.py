"""Render the review verdict from the findings instead of the model's prose.

The model writes the review summary in Chinese. Left alone, its verdict drifts
from the staged findings in two ways: the tally can claim two should-fix items
while listing three, and the verdict sentence can promise a merge the findings
do not allow. This module rewrites the first sentence under the 结论 heading from
the final review state and the tallies, keeping the prose the model wrote after
it. Staged inline comments carry the severity prefixes the review prompt
prescribes, so they are the authority for both.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Severity prefixes shared with the review prompt. A staged comment without a
# recognised prefix is counted as should-fix rather than dropped: silently
# losing a finding from the tally is worse than misclassifying it.
_SEVERITIES: tuple[tuple[str, str], ...] = (("阻塞项", "阻塞"), ("应改项", "应改"), ("建议", "建议"))
_DEFAULT_SEVERITY = "应改"

_CHINESE_DIGITS = "零一二三四五六七八九十"

_CONCLUSION_HEADING = re.compile(r"^##\s*结论\s*$", re.MULTILINE)


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


def stance(event: str, counts: dict[str, int]) -> str:
    """Render the verdict sentence the reader sees under 结论.

    Plain language only: the merge decision, and the tallies that produce it.
    Rank codes are deliberately absent — a reader cannot look them up.
    """
    blocking = [label for label in ("阻塞", "应改") if counts.get(label)]
    if event == "REQUEST_CHANGES":
        if not blocking:
            return "改掉下列各项后可合并。"
        clause = "、".join(f"{counts[label]} 条{label}" for label in blocking)
        return f"改掉 {clause}后可合并。"
    if event == "APPROVE":
        advice = counts.get("建议", 0)
        if advice:
            return f"可以合并，另有 {advice} 条建议不影响合并。"
        return "可以合并。"
    return "需要维护者决定是否纳入。"


def render_conclusion(body: str, counts: dict[str, int], event: str) -> str:
    """Replace the verdict sentence under 结论 with the one derived from findings.

    Only the first sentence of the section is replaced; prose the model wrote
    after it stays. A body without a 结论 heading is returned unchanged.
    """
    verdict = stance(event, counts)
    match = _CONCLUSION_HEADING.search(body)
    if match is None:
        return body
    start = match.end()
    # Skip the blank lines that separate the heading from its paragraph.
    while start < len(body) and body[start] in "\r\n":
        start += 1
    if start >= len(body):
        return f"{body.rstrip()}\n\n{verdict}"
    end = body.find("\n", start)
    if end == -1:
        end = len(body)
    paragraph = body[start:end]
    # Drop the model's own verdict sentence: everything up to the first full
    # stop, which is the clause carrying the rank and counts.
    stop = paragraph.find("。")
    rest = paragraph[stop + 1 :].strip() if stop != -1 else ""
    rebuilt = verdict if not rest else f"{verdict}{rest}"
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
    "render_conclusion",
    "severity_of",
    "stance",
    "strip_ai_footer",
]
