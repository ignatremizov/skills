# Semantic Code Analysis

Use these tools selectively after narrowing the changed area. Run Go commands from the relevant module root.

## Search Ladder

1. Use `rg` or `rg --files` for fast textual discovery.
2. Use `gopls` when correctness depends on Go symbol identity or types:
   - `gopls workspace_symbol '<query>'`
   - `gopls definition file.go:line:column`
   - `gopls references file.go:line:column`
   - `gopls implementation file.go:line:column`
   - `gopls call_hierarchy file.go:line:column`
   - `gopls check file.go`
3. Use `git log -S'<literal>'`, `git log -G'<regex>'`, and `git blame` to recover the history and ownership of an invariant or duplicated path.
4. Use `go list -deps`, `go mod why`, and `go mod graph` for dependency provenance.
5. Use `sqlc vet` for sqlc query/schema compatibility. Use PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` only against safe representative data when runtime query behavior matters.
6. For Vue/TypeScript, use `vue-tsc` and ESLint for configured semantic checks. Do not assume unused-file/export tools such as Knip are installed or correctly configured for dynamic routes and imports.

## Review-Only Go Linters

Inspect the repository's `.golangci.yml` first. Do not assume `make lint` enables a linter, and distinguish repository-default checks from ad-hoc review checks in the report.

To scout for substantial copied fragments in files changed from the actual target branch:

```bash
golangci-lint run --enable-only=dupl --issues-exit-code=0 \
  --new-from-merge-base=origin/develop --whole-files ./...
```

Replace `origin/develop` with the real PR target. `dupl` compares token sequences, so treat results as candidates. It can over-report table tests, builders, state matrices, and repetitive error handling, while missing semantically duplicated rules written differently.

Select additional linters only when the changed surface warrants them:

```bash
golangci-lint run \
  --enable-only=unused,gocritic,errorlint,bodyclose,noctx,rowserrcheck,sqlclosecheck,nilerr,nilnesserr \
  --issues-exit-code=0 ./...
```

Prefer smaller linter subsets and changed packages when possible. `staticcheck ./...` is useful when the repository does not already enable Staticcheck. Security review may use `gosec`, but it does not replace domain-specific authorization, privacy, money, or provider-boundary analysis.

## Validation Rules

- Treat tools as scouts, not decision-makers.
- Inspect both sides of a duplication finding and identify the duplicated knowledge or invariant, not merely similar syntax.
- Extract a shared helper only when it reduces current drift or complexity and has a clear owning layer.
- Do not generalize table tests, builders, or protocol/state-machine branches solely to silence `dupl`.
- Confirm apparent dead code with `gopls references`, build tags, generated wiring, reflection, framework registration, and external entry points before deletion.
- Confirm interface/call-graph findings with `gopls implementation` and `gopls call_hierarchy`.
- Report the exact command, scope, target branch, and whether the check was repository-default or ad hoc.
- Classify validated behavioral or current-scope maintainability defects normally; record unrelated cleanup as deferred rather than expanding the PR.
