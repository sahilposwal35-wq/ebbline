-- Query Q13: Which active rules have had no posting in 3 months?
-- Technique: NOT EXISTS anti-join against actual_txn

SELECT 
    r.rule_id, 
    r.account_id, 
    r.label,
    r.amount,
    r.start_date
FROM recurring_rule r
WHERE r.is_active = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM actual_txn a
      WHERE a.rule_id = r.rule_id
        AND a.txn_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
  );
