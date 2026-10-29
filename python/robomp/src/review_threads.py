"""Stable identity for inline review findings, and reuse across rounds.

Every finding the bot stages gets a fingerprint derived from the file and the
issue it describes, embedded as an HTML comment at the end of the comment body.
The fingerprint is what lets a later review recognise the same finding:

- a finding that is still present becomes a reply in its existing thread instead
  of a new thread;
- a finding that is no longer reported can be resolved;
- the thread ids are recorded so the next round knows where each finding lives.

The fingerprint deliberately ignores wording and exact line numbers, so a fix
that rephrases the finding or shifts lines does not split the thread.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_MARKER = "robomp-finding"
_MARKER_RE = re.compile(r"<!--\s*robomp-finding:\s*([0-9a-f]{12})\s*-->")

_SEVERITIES = ("阻塞项", "应改项", "建议")

# Strip the explanatory paragraphs and the suggested replacement. They change
# every round, so only the first sentence after the severity prefix identifies
# the finding.
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_WS_RE = re.compile(r"\s+")


def fingerprint(path: str, body: str) -> str:
    """Return a 12-hex-char id for a finding on `path` with the given body."""
    first = (body or "").strip().splitlines()
    head = first[0] if first else ""
    for prefix in _SEVERITIES:
        if head.startswith(prefix):
            head = head[len(prefix) :]
            break
    head = head.lstrip(" ：:")
    # Line numbers move as the diff evolves, so they cannot identify a finding.
    head = re.sub(r"第\s*\d+\s*行", "", head)
    # Drop backtick spans and code blocks so a wording tweak that swaps a
    # symbol for a literal does not create a second thread.
    head = _FENCE_RE.sub("", head)
    head = head.replace("`", "")
    head = _WS_RE.sub("", head).lower()
    digest = hashlib.sha256(f"{path}\n{head}".encode()).hexdigest()
    return digest[:12]


def with_fingerprint(body: str, fp: str) -> str:
    """Attach the fingerprint marker, replacing any stale one."""
    clean = strip_fingerprint(body).rstrip()
    return f"{clean}\n\n<!-- {_MARKER}: {fp} -->"


def strip_fingerprint(body: str) -> str:
    """Return the comment text without the marker line."""
    return _MARKER_RE.sub("", body or "").rstrip()


def fingerprint_of(body: str) -> str | None:
    """Read a fingerprint back from a comment body, if it carries one."""
    match = _MARKER_RE.search(body or "")
    return match.group(1) if match else None


@dataclass(slots=True, frozen=True)
class ThreadRef:
    """One of the bot's earlier review threads on a PR."""

    thread_id: str
    comment_id: int
    fingerprint: str
    path: str
    body: str
    resolved: bool


def match_fingerprints(
    staged: list[tuple[str, str]],
    threads: list[ThreadRef],
) -> tuple[dict[int, ThreadRef], list[ThreadRef], list[int]]:
    """Match new findings to existing threads.

    `staged` is an ordered list of (path, body) for this round's findings.
    Returns (matched_by_index, carried_threads, unmatched_indices). A thread
    matched this round cannot match again; the rest are candidates for
    resolution.
    """
    remaining = {t.fingerprint: t for t in threads if t.fingerprint and not t.resolved}
    used: set[str] = set()
    matched: dict[int, ThreadRef] = {}
    unmatched: list[int] = []
    for index, (path, body) in enumerate(staged):
        fp = fingerprint(path, body)
        thread = remaining.get(fp)
        if thread is None or fp in used:
            unmatched.append(index)
            continue
        matched[index] = thread
        used.add(fp)
    carried = [t for t in threads if t.fingerprint not in used and not t.resolved]
    return matched, carried, unmatched


__all__ = [
    "ThreadRef",
    "fingerprint",
    "fingerprint_of",
    "match_fingerprints",
    "strip_fingerprint",
    "with_fingerprint",
]
