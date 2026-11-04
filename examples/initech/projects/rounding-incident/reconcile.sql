-- Daily reconciliation: the sum of rounding remainders must stay inside
-- a small tolerance. Added after the rounding incident.

WITH daily AS (
    SELECT
        posted_date,
        SUM(amount)            AS raw_total,
        SUM(rounded_amount)    AS rounded_total,
        SUM(amount - rounded_amount) AS remainder_total,
        COUNT(*)               AS txn_count
    FROM ledger.transactions
    WHERE posted_date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY posted_date
)
SELECT
    posted_date,
    txn_count,
    raw_total,
    rounded_total,
    remainder_total,
    CASE
        WHEN ABS(remainder_total) <= txn_count * 0.005 THEN 'ok'
        ELSE 'INVESTIGATE'
    END AS verdict
FROM daily
ORDER BY posted_date DESC;
