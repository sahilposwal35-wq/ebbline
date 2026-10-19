-- Test T5: Rule ends before horizon
-- Rule 15 ended on 2026-05-01.
-- Expected: 0 occurrences appear after its end date.

SELECT COUNT(*) AS occ_after_end
FROM v_rule_occurrence 
WHERE source_id = 15 
  AND due_date > '2026-05-01';
