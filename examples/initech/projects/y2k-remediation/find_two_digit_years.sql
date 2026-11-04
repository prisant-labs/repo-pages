-- Find columns that still look like they hold two-digit years.
-- Run against each client reporting schema. Review every hit by hand:
-- some CHAR(2) columns are state codes, not years.

SELECT
    c.table_schema,
    c.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length
FROM information_schema.columns AS c
WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
  AND (
        (c.data_type IN ('character', 'character varying') AND c.character_maximum_length IN (2, 6))
     OR (c.data_type IN ('smallint', 'integer') AND c.column_name ~* '(^|_)(yy|yr|year)(_|$)')
     OR c.column_name ~* 'yymmdd'
  )
ORDER BY c.table_schema, c.table_name, c.column_name;

-- Count rows per year value in one suspect column, to confirm it holds years.
-- Replace the table and column before running.
SELECT stmt_yy, COUNT(*) AS row_count
FROM ledger.statement_header
GROUP BY stmt_yy
ORDER BY stmt_yy;
