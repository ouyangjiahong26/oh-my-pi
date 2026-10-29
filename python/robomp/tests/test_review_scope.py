"""Unit tests for per-repository review scope and file planning."""

from __future__ import annotations

from robomp.review_scope import is_ignored, language_rank, plan, scope_for


def test_lockfiles_and_binaries_are_ignored() -> None:
    scope = scope_for("cislunarspace/CODE-core")
    assert is_ignored("Cargo.lock", scope)
    assert is_ignored("assets/logo.png", scope)
    assert is_ignored("web/.vuepress/dist/index.html", scope)
    assert not is_ignored("e2m2e/api/models/design.py", scope)


def test_default_scope_for_unknown_repository() -> None:
    scope = scope_for("octo/widget")
    assert is_ignored("package-lock.json", scope)
    assert not is_ignored("src/app.ts", scope)


def test_language_priority_orders_reading_sequence() -> None:
    scope = scope_for("cislunarspace/CODE")
    assert language_rank("src/main.rs", scope) < language_rank("web/readme.md", scope)
    assert language_rank("unknown.xyz", scope) > language_rank("docs/a.md", scope)


def test_plan_orders_review_files_and_lists_skipped() -> None:
    plan_result = plan(
        ["web/glossary/index.md", "Cargo.lock", "crates/e2m2e/src/lib.rs", "assets/logo.png"],
        "cislunarspace/CODE-core",
    )
    assert plan_result.review[0] == "crates/e2m2e/src/lib.rs"
    assert "web/glossary/index.md" in plan_result.review
    assert plan_result.skipped == ("Cargo.lock", "assets/logo.png")


def test_plan_with_no_ignorable_files() -> None:
    result = plan(["a.py", "b.py"], "octo/widget")
    assert result.review == ("a.py", "b.py")
    assert result.skipped == ()
