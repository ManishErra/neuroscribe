-- Read-only checks: run in Supabase SQL Editor after applying create_reports_table.sql

SELECT to_regclass('public.reports') AS reports_table;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'reports'
ORDER BY ordinal_position;

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'reports'
ORDER BY indexname;
