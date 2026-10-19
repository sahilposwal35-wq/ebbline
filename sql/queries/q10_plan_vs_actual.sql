-- Query Q10: Planned vs actual per rule per month with a 3-month average
-- Technique: Aggregate, AVG() OVER with 3-row frame
-- Parameters: @rule_id

SELECT 
    m.rule_id, 
    m.ym, 
    m.planned, 
    m.actual,
    (m.actual - m.planned) AS variance,
    AVG(m.actual) OVER (
        PARTITION BY m.rule_id 
        ORDER BY m.ym
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS avg_3m
FROM (
    SELECT 
        r.rule_id, 
        DATE_FORMAT(a.txn_date, '%Y-%m') AS ym,
        r.amount AS planned, 
        SUM(a.amount) AS actual
    FROM recurring_rule r
    JOIN actual_txn a ON a.rule_id = r.rule_id
    WHERE (@rule_id IS NULL OR r.rule_id = @rule_id)
    GROUP BY r.rule_id, ym, r.amount
) m
ORDER BY m.rule_id, m.ym;
