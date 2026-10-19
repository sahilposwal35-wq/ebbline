-- Test T2: Leap-year 29 Feb start
-- Expected: Clamps to 28 Feb in non-leap years (2025, 2026, 2027), returns 29 Feb in leap years (2024, 2028)

SELECT due_date 
FROM v_rule_occurrence 
WHERE source_id = 10 
  AND due_date BETWEEN '2024-01-01' AND '2028-12-31' 
ORDER BY due_date;
