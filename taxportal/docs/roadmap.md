# TaxPortal1040 Roadmap

The spec calls for a complete production platform. Delivering it in one
pass would be unsafe for tax data. This roadmap sequences the work by
blast radius so each phase is reviewable, testable, and shippable.

## Phase 1 — Foundations *(this commit)*
- Monorepo, calc engine for 1040 L1–38, Prisma schema with RLS,
  Terraform network + data modules, CI pipeline.

## Phase 2 — Full calc surface
- Schedules 1, 2, 3, A, B, C, D, E, EIC, F, H, J, R, SE, 8812.
- Forms 2210, 2441, 2555, 4562, 4684, 4797, 4868, 4952, 5329, 6251, 8283,
  8582, 8606, 8615, 8801, 8814, 8815, 8824, 8829, 8839, 8853, 8863, 8867,
  8879, 8880, 8889, 8915-F, 8938, 8949, 8958, 8959, 8960, 8962, 8990,
  8995, 8995-A, 9465, FinCEN 114.
- Diagnostics rules engine (safe harbor, AMT, NIIT, Add'l Medicare, §199A,
  §469, §465, §461(l), basis tracking, §6038D, FBAR, PFIC, §6038).
- IRS ATS regression scenarios.

## Phase 3 — API, Auth, RBAC
- NestJS modules, controllers, OpenAPI 3.1, TypeScript SDK.
- Auth.js (password + WebAuthn + TOTP; SAML/OIDC SSO).
- CASL policies + Prisma middleware that sets `app.current_firm_id`.

## Phase 4 — Web and client portal
- Next.js 14 preparer walkthrough (stepper, help panels).
- Client portal (plain-English walkthrough, documents, messaging, 8879).
- shadcn/ui components, TanStack Query, Zustand, RHF + Zod.

## Phase 5 — Intake and extraction
- Signed-URL upload, ClamAV scan, SHA-256, fingerprint dedup.
- Textract / Document Intelligence + Claude/GPT multimodal fallback.
- Client attestation, correction workflow.

## Phase 6 — Review module + messaging
- Five-phase checklist persisted to DB.
- Review comments first-class with urgency/confidence/rollover.
- Two-way encrypted messaging with attachments + read receipts.

## Phase 7 — E-file
- MeF XML generation + schema + business-rule validation.
- Submission ID algorithm, 8879 signature capture (KBA).
- Transmitter interface + mock/default production adapters.
- ACK parsing and rejection remediation UI.

## Phase 8 — AI
- Provider abstraction (OpenAI, Anthropic).
- Preparer (full context) and client (scoped) assistants.
- Tool use (lookup-line, lookup-doc, search-authority, etc.).
- RAG corpus: IRC, CFR, forms/pubs, RR/RP/Notices, Tax Court since 2000.
- pgvector, Voyage or OpenAI embeddings, recency metadata.
- PII redaction, prompt-injection defenses, token budgets.

## Phase 9 — State returns
- NC (D-400), SC (SC1040), VA (760), GA (500), TN stub, NY (IT-201/203),
  CA (540/540NR), FL residency detection, scaffolding module.

## Phase 10 — Observability, compliance, readiness
- OpenTelemetry + Grafana + Sentry + pino.
- WISP document, IR playbook, pen-test plan, DAST in CI, state breach
  notification template library.
- SOC 2 Type II evidence pack structure.
