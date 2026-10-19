-- Test T11: Account with no breach returns NULL for first_breach_date and 0 for days_below_buffer
-- Account 2: Emergency Reserve (Never Breaches)

CALL build_projection(1, 2, 365, @run_id_t11);

SELECT 
    run_id, 
    account_id, 
    first_breach_date, 
    days_below_buffer, 
    min_balance >= 20000.00 AS stays_above_buffer
FROM projection_run 
WHERE run_id = @run_id_t11;
