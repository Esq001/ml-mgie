# ADR 0001: Monorepo with an isolated, pure calculation package

**Status**: Accepted (2026-04-20)

## Context

The calculation engine must be deterministic, easily auditable, and
100%-testable in isolation. It also needs to run in three places: the
API (for interactive preparation), the worker (for bulk recomputation
after document changes), and CI (for regression tests against IRS ATS
scenarios and property-based tests). Running the same engine bytes in
every location is a SOC 2 change-management win.

## Decision

- Use a pnpm + Turborepo monorepo with a dedicated `@taxportal/calc`
  package.
- Calc is pure TypeScript: no Prisma imports, no network IO, no
  filesystem. Its only runtime dependency is `decimal.js`.
- Every line result carries a `Provenance` record — the inputs, the
  formula in plain English, and one or more `AuthorityCitation`s. The
  downstream UI renders this as a "show your work" panel; the audit log
  stores it verbatim.
- Money values are a custom `Money` class backed by `Decimal` with
  deliberate rounding semantics. The outer world uses whole-dollar
  amounts (IRS convention) but the engine preserves sub-cent precision
  until the final `roundToDollar()` call per line.

## Consequences

- Upgrading Prisma, Next.js, or NestJS never requires changes to calc.
- Calc coverage thresholds can be pinned at 90%+ without dragging in
  framework boilerplate.
- Running a nightly IRS-ATS regression job against `@taxportal/calc`
  alone is trivial (no DB spin-up).
- Calc must not depend on the Prisma types — the API layer translates
  `Return` / `LineItem` rows into calc input structs at call time. That
  adds a thin adapter but keeps the engine portable.
