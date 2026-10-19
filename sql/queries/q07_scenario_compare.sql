-- Query Q7: How do two scenarios differ?
-- Technique: Join of two latest runs from v_latest_run
-- Parameters: @scenario_a, @scenario_b, @account_id

SELECT 
    ra.account_id,
    ra.scenario_id AS scenario_a,
    rb.scenario_id AS scenario_b,
    ra.min_balance AS min_balance_a,
    rb.min_balance AS min_balance_b,
    (rb.min_balance - ra.min_balance) AS min_balance_delta,
    ra.first_breach_date AS first_breach_a,
    rb.first_breach_date AS first_breach_b,
    DATEDIFF(rb.first_breach_date, ra.first_breach_date) AS breach_shift_days,
    ra.days_below_buffer AS days_below_a,
    rb.days_below_buffer AS days_below_b,
    (rb.days_below_buffer - ra.days_below_buffer) AS days_below_delta
FROM v_latest_run ra
JOIN v_latest_run rb ON ra.account_id = rb.account_id 
                    AND ra.account_id = @account_id
                    AND ra.scenario_id = @scenario_a 
                    AND rb.scenario_id = @scenario_b;
