-- Test T3: Weekly rule, every 2 weeks
-- Expected: Consecutive occurrences spaced by exactly 14 days

SELECT 
    due_date, 
    DATEDIFF(due_date, LAG(due_date) OVER (ORDER BY due_date)) AS diff_days
FROM v_rule_occurrence 
WHERE source_id = 6 
  AND due_date BETWEEN '2026-10-01' AND '2026-12-31' 
ORDER BY due_date;
