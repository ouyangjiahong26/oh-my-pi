"""Per-repository review scope: which paths to read, and in what order.

A PR review should spend its budget on files a human would actually read. Two
deterministic helpers:

- `scope_for(repo)` returns the repository's ignore globs and language order.
  Generated files, lockfiles, vendored trees and binary assets are never worth
  inline review; the caller still lists them so the reader knows they were
  skipped deliberately.
- `plan(files, repo)` partitions the changed-file list into reviewable files in
  reading order and the skipped set, so a large PR can be summarised instead of
  dumped in full.

The table is data, not behaviour: a repository without an entry falls back to
sensible defaults. Nothing here runs a command.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Iterable


@dataclass(slots=True, frozen=True)
class Scope:
    """Ignore globs and language priority for one repository family."""

    ignore_globs: tuple[str, ...]
    languages: tuple[str, ...]
    # Paths that should still be listed but never opened line by line.
    skip_note: str = "生成产物、锁文件或二进制资产，评审不逐行展开"


_DEFAULT_IGNORE: tuple[str, ...] = (
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "uv.lock",
    "poetry.lock",
    "bun.lock",
    "go.sum",
    "composer.lock",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
    "dist/*",
    "build/*",
    "node_modules/*",
    ".venv/*",
    "vendor/*",
)

# The sites and tools share these; keep the list short so it stays predictable.
_SCOPE_BY_OWNER: dict[str, Scope] = {
    "cislunarspace": Scope(
        ignore_globs=_DEFAULT_IGNORE
        + (
            "web/.vuepress/dist/*",
            "web/.vuepress/.cache/*",
            "web/.vuepress/.temp/*",
            "web/glossary/_generated/*",
            "**/*.generated.*",
            "crates/**/target/*",
            "**/fixtures/**/*.json",
        ),
        languages=(
            ".rs",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".vue",
            ".toml",
            ".yaml",
            ".yml",
            ".json",
            ".md",
        ),
    ),
}

_DEFAULT_SCOPE = Scope(ignore_globs=_DEFAULT_IGNORE, languages=(".rs", ".py", ".ts", ".js", ".toml", ".json", ".md"))


def scope_for(repo: str) -> Scope:
    owner = (repo or "").split("/", 1)[0].lower()
    return _SCOPE_BY_OWNER.get(owner, _DEFAULT_SCOPE)


def is_ignored(path: str, scope: Scope) -> bool:
    """True when the path matches any ignore glob for the repository."""
    if not path:
        return False
    for pattern in scope.ignore_globs:
        if fnmatch(path, pattern):
            return True
        # Treat a bare directory glob as covering everything under it.
        if pattern.endswith("/*") and path.startswith(pattern[:-1]):
            return True
    return False


def language_rank(path: str, scope: Scope) -> int:
    """Lower means read earlier. Unknown extensions go last."""
    lower = path.lower()
    for index, ext in enumerate(scope.languages):
        if lower.endswith(ext):
            return index
    return len(scope.languages)


@dataclass(slots=True, frozen=True)
class Plan:
    """Ordered reviewable files and the paths skipped on purpose."""

    review: tuple[str, ...]
    skipped: tuple[str, ...]


def plan(paths: Iterable[str], repo: str) -> Plan:
    """Order reviewable paths by language priority, then by path."""
    scope = scope_for(repo)
    review: list[str] = []
    skipped: list[str] = []
    for path in paths:
        if is_ignored(path, scope):
            skipped.append(path)
        else:
            review.append(path)
    review.sort(key=lambda p: (language_rank(p, scope), p))
    return Plan(review=tuple(review), skipped=tuple(sorted(skipped)))


__all__ = ["Plan", "Scope", "is_ignored", "language_rank", "plan", "scope_for"]
