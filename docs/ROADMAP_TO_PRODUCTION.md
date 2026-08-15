# Roadmap to production

The MVP deliberately optimizes for a reviewable end-to-end flow. Work should proceed in this order.

## P0 — correctness and durability

1. Replace the in-memory store and preview-token dictionary with PostgreSQL.
2. Wrap mutations, schedule recalculation, and revision creation in one transaction.
3. Store immutable revisions and changesets; expose multi-step undo/redo and restore.
4. Add idempotency keys, optimistic concurrency using revision or ETag, backups, and restore drills.
5. Add working calendars, holidays, time zones, milestones, and explicit dependency lag.
6. Move large Excel parsing and export to bounded background jobs with file size and row limits.
7. Add contract, property-based scheduler, load, and browser end-to-end tests.

Risk: concurrent updates currently overwrite process memory and disappear on restart. This blocks production use.

## P1 — security and tenancy

1. OIDC/SSO authentication, tenant isolation, project RBAC, and row-level authorization.
2. CSRF strategy, strict CORS/CSP, upload malware scanning, MIME/signature checks, and rate limits.
3. Managed secret storage and key rotation; never expose provider keys to the browser.
4. Tamper-evident audit log for imports, exports, manual edits, agent tool calls, and undo.
5. Privacy review, retention controls, data export/deletion, and dependency/SBOM scanning.

## P1 — real AI and MCP safety

1. Replace the mock parser with an OpenRouter adapter selected by environment.
2. Give the model read-only project context and strict, narrow MCP tool schemas; retain deterministic scheduling.
3. Add confirmation for destructive, bulk, or ambiguous changes and show a proposed diff before commit.
4. Version prompts and schemas; trace latency and tool outcomes without storing hidden reasoning.
5. Build at least 20 fixed intent regressions plus adversarial tests for prompt injection and invalid tool calls.
6. Add timeout, retry, provider fallback, spend budgets, and per-tenant quotas.
7. Measure intent accuracy, valid-tool-call rate, correction and undo rate, latency, and cost.

Risk: natural-language ambiguity can produce valid but unintended edits. Preview, audit, revision history, and risk-based confirmation are required together.

## P2 — scale and product depth

- Real-time collaboration, presence, comments, notifications, and conflict resolution
- Virtualization and incremental scheduling for projects with tens of thousands of tasks
- Portfolio/resource views and cross-project dependencies
- Jira, Linear, Microsoft Project, and Google Sheets integrations
- Accessibility audit, localization, mobile task review, observability, SLOs, and incident runbooks

## Exit criteria

Production readiness requires durable transactional state, tested restore, tenant isolation, full auditability, controlled AI mutations, operational dashboards and alerts, and successful security and accessibility reviews.
