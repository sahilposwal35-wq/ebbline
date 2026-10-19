-- Query Q1: Which dated events fall in the horizon?
-- Technique: Recursive CTE via v_rule_occurrence, UNION ALL with one_off_event
-- Parameters: @account_id, @horizon_start, @horizon_end

SELECT 
    source_type,
    source_id,
    account_id,
    category_id,
    label,
    amount,
    due_date
FROM v_rule_occurrence
WHERE account_id = @account_id
  AND due_date BETWEEN @horizon_start AND @horizon_end

UNION ALL

SELECT 
    'EVENT' AS source_type,
    event_id AS source_id,
    account_id,
    category_id,
    label,
    amount,
    event_date AS due_date
FROM one_off_event
WHERE account_id = @account_id
  AND event_date BETWEEN @horizon_start AND @horizon_end

ORDER BY due_date, source_type, source_id;
