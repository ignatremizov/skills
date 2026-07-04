---
name: backend-coding
description: Use for backend coding and review tasks involving APIs, services, databases, persistence, queues, workers, auth, security/privacy, telemetry/observability, migrations, distributed or async flows, performance, or server-side business logic.
---

# Backend Coding

Use this skill when building or reviewing backend systems.

## System Boundaries

- Preserve service boundaries and dependency direction; avoid reaching across layers for short-term convenience.
- Keep API, domain, persistence, and transport concerns separated unless the codebase intentionally uses a different pattern.
- Prefer explicit state transitions and invariants over implicit side effects.
- Use existing repository patterns, framework conventions, and local helper APIs before introducing a new abstraction.
- Add abstractions only when they reduce real complexity, meaningful duplication, or clearly match an established local pattern.

## Correctness

- Treat data integrity, idempotency, retries, concurrency, authorization, observability, and telemetry as first-class design constraints.
- For distributed or async flows, reason about duplicate delivery, partial failure, cancellation, ordering, and cleanup.
- Pair schema changes with the required migrations, generated artifacts, fixtures, or compatibility updates.
- Keep errors useful at the boundary where they are observed: return actionable errors to callers and log enough context for operators without leaking secrets.
- Use structured APIs, parsers, and typed payloads instead of ad hoc string manipulation when the codebase or platform gives you a reasonable option.

## Security And Privacy

- Treat security and privacy as part of correctness.
- Protect secrets, credentials, tokens, and personal or customer data.
- Validate authorization boundaries and tenant/account scoping.
- Avoid leaking sensitive data in logs, errors, telemetry, analytics, traces, generated files, or test fixtures.
- Minimize data exposure and retention unless the product or repo explicitly requires it.

## Performance

- Watch hot paths, unbounded queries, N+1 access patterns, unnecessary network calls, excessive memory use, and work that scales poorly with input size.
- Prefer bounded batch sizes, pagination, streaming, backpressure, or queueing where input size can grow.
- Avoid adding expensive synchronous work to latency-sensitive request paths unless the tradeoff is explicit and acceptable.

## Telemetry

- Preserve or add meaningful telemetry for important behavior changes.
- Prefer metrics, traces, structured logs, audit events, and dashboards that reflect states and failure modes operators need to see.
- Make telemetry cardinality and payload size intentional; avoid high-cardinality labels or large free-form payloads unless the system already supports them.

## Validation

- Use existing test harnesses, factories, fixtures, and integration helpers before adding new ones.
- Cover changed behavior at the level where regressions are most likely: unit tests for local pure logic, integration tests for boundary contracts and multi-component behavior.
- Include negative or edge-case coverage when authorization, idempotency, data integrity, concurrency, or migration behavior changed.
