-- Test T1: Monthly rule starting 31 Jan
-- Expected: Jan 31, Feb 28, Mar 31 (month-end clamp with no drift)

SELECT due_date 
FROM v_rule_occurrence 
WHERE source_id = 9 
  AND due_date BETWEEN '2026-01-01' AND '2026-04-01' 
ORDER BY due_date;
