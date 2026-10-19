-- Test T6: Rule starts after horizon
-- Insert temporary rule starting in 2030, check horizon up to 2027.
-- Expected: 0 occurrences appear in the 2026-2027 horizon.

SELECT COUNT(*) AS occ_future_start
FROM v_rule_occurrence 
WHERE start_date > '2028-12-31' 
  AND due_date <= '2027-12-31';
