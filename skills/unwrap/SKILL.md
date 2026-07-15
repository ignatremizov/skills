---
name: unwrap
description: Use when asked to unwrap Markdown, remove soft or hard source line wrapping, place prose paragraphs or list items on single source lines, or update and validate the canonical unwrap.pl Markdown utility.
---

# Unwrap Markdown

Joins soft-wrapped Markdown prose while preserving headings, front matter, tables, fenced and indented code, block quotes, explicit hard breaks, newline style, file permissions. Avoids inserting spaces into wrapped paths and expressions after `/`, `(`, `[`, `->`, `=>`, or supported Unicode arrows.

`~/code/skills/skills/unwrap/scripts/unwrap.pl` is the script, with a `~/.local/bin/unwrap` symlink existing on `PATH`.

## Usage

Get help:

```bash
unwrap --help
```

Preview one file on stdout:

```bash
unwrap path/to/file.md
```

Use it as a filter:

```bash
unwrap < path/to/file.md
```

Update one or more files atomically:

```bash
unwrap --in-place README.md docs/*.md
```

Inspect the result:

```bash
git diff --check -- README.md docs/
git diff -- README.md docs/
```

## Workflow

1. Confirm the target is Markdown and identify whether the request applies to the whole file or only a section.
2. Check the worktree before in-place edits so unrelated changes are not mistaken for unwrap output.
3. Prefer a stdout preview when the document contains unusual Markdown or embedded formats.
4. Run `--in-place` only on the requested files.
5. Review the diff. The intended change is line joining, not wording, punctuation, ordering, or code modification.
6. Run `git diff --check` and any repository-specific documentation validation.

The command is idempotent. Verify an already-unwrapped file when useful:

```bash
unwrap path/to/file.md | cmp -s - path/to/file.md
```

## Updating The Script

Edit the script when an observed Markdown construct is handled incorrectly or a requested CLI capability is missing. Do not generalize speculatively.

Before editing:

1. Capture the smallest input that reproduces the problem.
2. State which Markdown structure and semantics must be preserved.
3. Check whether the issue belongs to prose joining, block classification, newline handling, or atomic file replacement.

Preserve these interface guarantees:

- No arguments reads stdin and writes stdout.
- One file without `--in-place` writes stdout.
- `--in-place` accepts one or more files and replaces them atomically.
- Multiple files without `--in-place` fail instead of concatenating ambiguous output.
- Symlink targets, source permissions, CRLF/LF style, fenced content, and explicit Markdown hard breaks remain intact.
- Wrapped paths and inline expressions retain adjacency after `/`, `(`, `[`, `->`, `=>`, `→`, `⟶`, `←`, `↔`, `⇒`, and `⟹`.
- Bulleted lists recognize `-`, `+`, `*`, and `•`.
- A second run produces no further changes.

After editing, run at least:

```bash
perl -c "~/code/skills/skills/unwrap/scripts/unwrap.pl"
unwrap --help
```

Exercise the affected construct plus representative front matter, backtick and tilde fences, numbered and bulleted lists including `•`, tables with and without leading pipes, block quotes, indented code, explicit two-space and backslash hard breaks, wrapped connector cases, LF, CRLF, stdout mode, and atomic in-place mode. Then run the utility against a real target twice and confirm the second pass is identical.
