"""Unit tests for review-thread identity and matching."""

from __future__ import annotations

from robomp.review_threads import (
    ThreadRef,
    fingerprint,
    fingerprint_of,
    match_fingerprints,
    strip_fingerprint,
    with_fingerprint,
)


def _thread(fp: str, *, resolved: bool = False, tid: str = "T1") -> ThreadRef:
    return ThreadRef(thread_id=tid, comment_id=10, fingerprint=fp, path="src/app.py", body="body", resolved=resolved)


def test_fingerprint_is_stable_across_marker_roundtrip() -> None:
    body = "应改项：第 42 行在判空之前解引用 cfg。"
    fp = fingerprint("src/app.py", body)
    assert len(fp) == 12
    marked = with_fingerprint(body, fp)
    assert fingerprint("src/app.py", marked) == fp
    assert strip_fingerprint(marked) == body
    assert fingerprint_of(marked) == fp


def test_fingerprint_ignores_line_numbers_and_wording_of_example() -> None:
    a = "应改项：第 42 行在判空之前解引用 `cfg`。"
    b = "应改项：第 77 行在判空之前解引用 `cfg`。"
    assert fingerprint("src/app.py", a) == fingerprint("src/app.py", b)


def test_fingerprint_differs_by_path_or_finding() -> None:
    body = "应改项：解引用 cfg。"
    assert fingerprint("a.py", body) != fingerprint("b.py", body)
    assert fingerprint("a.py", body) != fingerprint("a.py", "应改项：另一个问题。")


def test_with_fingerprint_replaces_stale_marker() -> None:
    marked = with_fingerprint("body", "a" * 12)
    again = with_fingerprint(marked, "b" * 12)
    assert again.count("robomp-finding") == 1
    assert fingerprint_of(again) == "b" * 12


def test_match_reuses_threads_and_lists_carried_ones() -> None:
    body = "应改项：解引用 cfg。"
    fp = fingerprint("src/app.py", body)
    threads = [_thread(fp), _thread("f" * 12, tid="T2")]
    matched, carried, unmatched = match_fingerprints([("src/app.py", body)], threads)
    assert matched[0].thread_id == "T1"
    assert carried[0].thread_id == "T2"
    assert unmatched == []


def test_match_leaves_new_findings_unmatched() -> None:
    threads = [_thread("f" * 12)]
    matched, carried, unmatched = match_fingerprints([("src/app.py", "应改项：新问题。")], threads)
    assert matched == {}
    assert unmatched == [0]
    assert len(carried) == 1


def test_match_skips_resolved_threads() -> None:
    body = "应改项：解引用 cfg。"
    fp = fingerprint("src/app.py", body)
    threads = [_thread(fp, resolved=True)]
    matched, carried, unmatched = match_fingerprints([("src/app.py", body)], threads)
    assert matched == {}
    assert carried == []
    assert unmatched == [0]
