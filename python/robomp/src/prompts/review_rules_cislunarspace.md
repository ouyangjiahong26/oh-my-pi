Deterministic review rules for cislunarspace content PRs.

These are facts you can check by reading the diff. They never need a command.
Apply them in Phase 2 alongside the general correctness review. Each violation is
a finding with its line reference, the same as any other finding. Do not repeat a
finding in prose that you have already staged inline.

Scope: this file only applies to cislunarspace glossary, chapter, and site-content
changes. It says nothing about application code.

## Bibliography and citation

- Every `\cite{key}` used in a changed Markdown file must have a matching entry in
  `web/.vuepress/ref.bib`. A missing key is 应改项.
- New bibliography keys follow `lowercaseSurnameFirstSignificantTitleWordYear`.
  The same Zotero item must reuse its existing cite key across the site.
- Cite only material you can point to in the diff. Do not invent entries.

## Glossary frontmatter

- `title` is at most 66 characters.
- `aliases` is non-empty and has no duplicates.
- Every `related[].ref` points to an existing page or glossary entry, and
  `relation` is one of `broader`, `transfer`, `related`.
- When an entry is added, removed, or renamed, the section index and the site
  counters are updated in the same PR, and reverse links in related entries are
  updated. Missing reverse-link updates are 应改项.

## Prose and punctuation

- Chinese prose uses full-width Chinese punctuation. No em dashes, semicolons,
  arrows, markdown bold, or emoji in prose. Lists use `、` and the last item is
  not introduced by 和 or 与.
- Inline code, file names, commands, formulas, URLs, and bibliography entries
  keep their original punctuation.
- Do not infer Chinese names of people or institutions from pinyin or foreign
  spellings. The library's own Chinese spelling is authoritative; when it is not
  available, say so instead of guessing a translation.
- Numbers with units use the national-standard form: a space between value and
  unit symbol, for example `200 ms` or `64 MB`.

## Deterministic checks are already covered elsewhere

- Lint, link checking, and build are CI's job. Do not re-derive their outcome in
  the review body. If a rule above conflicts with what CI would say, the review
  still reports the rule violation and names it as such.
