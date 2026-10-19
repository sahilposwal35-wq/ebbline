-- Test T4: Yearly rule via every_n = 12
-- Expected: Exactly 1 occurrence per year

SELECT COUNT(*) AS occ_count
FROM v_rule_occurrence 
WHERE source_id = 11 
  AND due_date BETWEEN '2026-10-01' AND '2027-10-01';
