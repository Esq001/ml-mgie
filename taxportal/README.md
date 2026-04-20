# TaxPortal1040

Multi-tenant Form 1040 client workflow platform for a CPA firm. This repo
lives inside the `ml-mgie` repository on the
`claude/build-taxportal-app-wSxLc` branch while Phase 1 is stabilized.

## Status: Phase 1 scaffold

What is in this commit:

- **Monorepo**: pnpm + Turborepo layout (`apps/`, `packages/`, `infra/`, `docs/`).
- **Calc engine (`@taxportal/calc`)**: pure TypeScript Form 1040 computation
  for tax year 2025, lines 1–38, with provenance records and authority
  citations. 34 passing unit + property-based tests; 99.9% line coverage,
  100% function coverage on non-input modules.
- **Prisma schema (`@taxportal/db`)**: firms, users, clients, engagements,
  document uploads, extracted documents, returns, line items, state
  returns, carryforwards, estimated payments, review phases, review
  comments, e-file packages, messages, AI interactions, append-only audit
  log. First migration enables row-level security on every tenant-bearing
  table.
- **Terraform baseline**: `modules/network` (VPC, subnets, NAT, flow logs)
  and `modules/data` (KMS CMK, RDS PostgreSQL 16, ElastiCache Redis 7,
  encrypted S3 bucket with versioning + lifecycle). Staging and production
  workspaces.
- **CI**: GitHub Actions workflow for calc typecheck + tests + coverage,
  Semgrep SAST, tfsec IaC scan, gitleaks secret scan.
- **Seed**: demo firm, admin / 2 preparers / reviewer, five client fact
  patterns.

## Status: what this commit does **not** deliver

The spec describes a full production SOC 2 / IRS Pub 1345-ready system.
That is roughly 6–12 months of team work. The following are explicit
known gaps, to be addressed in follow-up phases:

1. Next.js 14 web app (preparer walkthrough, client portal, messaging UI).
2. NestJS controllers, Auth.js integration, OpenAPI generation, CASL policies.
3. BullMQ worker and ClamAV upload scanning.
4. OCR / extraction pipeline (Textract / Document Intelligence + LLM fallback).
5. All schedules and forms beyond Form 1040 lines 1–38.
6. State return modules (NC, SC, VA, GA, TN, NY, CA, FL).
7. MeF XML generation, validation, and transmitter integration.
8. AI abstraction (OpenAI + Anthropic), RAG corpus ingestion, guardrails.
9. ECS Fargate / CloudFront / WAF / Route 53 Terraform workspaces.
10. Playwright E2E, Supertest integration tests, k6 load tests, DAST.
11. WISP document, incident response runbooks, pen test plan.

See `docs/roadmap.md` for the full sequencing.

## Running what exists

```bash
cd taxportal/packages/calc
npm install
npx tsc -p tsconfig.json --noEmit
npx vitest run --coverage
```

## Repository layout

```
taxportal/
  apps/
    web/        Next.js 14 (placeholder)
    api/        NestJS (placeholder with calc integration point)
    worker/     BullMQ worker (placeholder)
  packages/
    calc/       Pure calculation engine (Phase 1 complete for 1040 L1–38)
    db/         Prisma schema + RLS migration + seed
    ui/         (placeholder)
    efile/      (placeholder)
    ai/         (placeholder)
    config/     (placeholder)
  infra/
    terraform/  network + data modules, staging + production envs
  docs/
    adr/        Architecture decision records
    roadmap.md  Phase plan
```

## License

See `../LICENSE.txt` in the parent repository.
