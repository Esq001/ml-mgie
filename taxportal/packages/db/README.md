# @taxportal/db

Prisma schema, migrations, and seed data for TaxPortal1040.

## Public surface

- `prisma/schema.prisma` — all models. Every tenant-bearing table has
  `firmId`, `createdAt`, `updatedAt`, `createdBy`, `updatedBy`, `deletedAt`.
- `prisma/migrations/20250420000000_rls/` — enables PostgreSQL
  row-level security on every tenant-bearing table.
- `prisma/seed.ts` — demo firm, 4 users, 5 clients, engagements.

## Running migrations

```bash
export DATABASE_URL=postgres://taxportal:devpass@localhost:5432/taxportal
npx prisma migrate dev
npx tsx prisma/seed.ts
```

## Tenancy enforcement

The API sets `SET LOCAL app.current_firm_id = '<uuid>'` on every
transaction. A missing GUC causes the RLS policy to return zero rows,
which surfaces as a loud error rather than silently leaking data.
