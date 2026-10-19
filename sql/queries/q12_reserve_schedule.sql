-- Query Q12: How much to set aside monthly for yearly and quarterly bills?
-- Technique: Division by period months, query on v_reserve_schedule
-- Parameters: @account_id

SELECT 
    rule_id,
    label,
    total_obligation,
    unit,
    every_n,
    period_months,
    monthly_set_aside
FROM v_reserve_schedule
WHERE account_id = @account_id
ORDER BY monthly_set_aside DESC;
