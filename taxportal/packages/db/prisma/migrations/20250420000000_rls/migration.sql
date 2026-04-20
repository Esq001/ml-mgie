-- Row-level security policies for multi-tenant isolation.
--
-- The API layer sets `SET app.current_firm_id = '<uuid>'` on every
-- transaction (via PgBouncer session pooling or a Prisma middleware that
-- prefixes every query with SET LOCAL). RLS policies match on that GUC.
--
-- This migration is intentionally hand-written; Prisma does not model
-- RLS. It is applied by `prisma migrate deploy` alongside schema DDL.

-- Helper GUC accessor.
CREATE OR REPLACE FUNCTION current_firm_id() RETURNS uuid
  LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_firm_id', true), '')::uuid;
$$;

-- Apply RLS to every tenant-bearing table.
DO $$
DECLARE
  tbl text;
  tenant_tables text[] := ARRAY[
    'firm_users', 'clients', 'engagements',
    'taxpayer_profiles', 'dependents',
    'document_uploads', 'extracted_documents',
    'returns', 'line_items', 'state_returns', 'carryforwards',
    'estimated_payments',
    'review_phases', 'review_comments',
    'efile_packages',
    'message_threads', 'messages',
    'ai_interactions',
    'audit_log'
  ];
BEGIN
  FOREACH tbl IN ARRAY tenant_tables LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', tbl);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY;', tbl);
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I;', tbl);
    EXECUTE format(
      'CREATE POLICY tenant_isolation ON %I
         USING (firm_id = current_firm_id())
         WITH CHECK (firm_id = current_firm_id());',
      tbl
    );
  END LOOP;
END$$;

-- The firms table itself is readable only to a privileged app role.
ALTER TABLE firms ENABLE ROW LEVEL SECURITY;
ALTER TABLE firms FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS firms_self_only ON firms;
CREATE POLICY firms_self_only ON firms
  USING (id = current_firm_id())
  WITH CHECK (id = current_firm_id());
