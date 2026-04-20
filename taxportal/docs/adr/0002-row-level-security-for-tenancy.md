# ADR 0002: PostgreSQL row-level security for tenant isolation

**Status**: Accepted (2026-04-20)

## Context

Every business table carries a `firm_id`. Application code will enforce
tenancy checks at the CASL policy layer, but a single missing check in
a controller would leak taxpayer data across firms — the worst possible
failure mode for this product.

## Decision

- Every tenant-bearing table has `ROW LEVEL SECURITY` enabled and
  forced.
- A single policy `tenant_isolation` matches `firm_id = current_firm_id()`
  where `current_firm_id()` reads the `app.current_firm_id` GUC.
- The API sets the GUC at the start of every transaction via a Prisma
  middleware that runs `SET LOCAL app.current_firm_id = $1` from the
  authenticated session's claim. PgBouncer is configured in session
  pooling mode on the transaction boundary to preserve the GUC.
- The `firms` table itself uses a `firms_self_only` policy so even a
  compromised API key scoped to one firm cannot read another firm's
  metadata.

## Consequences

- A forgotten `WHERE firm_id = ?` clause in application code can no
  longer leak cross-tenant rows. The database refuses the read.
- Ops personnel performing one-off queries must use a privileged role
  that bypasses RLS, which is audit-logged.
- Prisma raw queries must still run inside a transaction that sets the
  GUC. This is enforced by a wrapper helper in `@taxportal/db`.
