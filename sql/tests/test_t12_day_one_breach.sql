-- Test T12: Breach on Day 1
-- Creates temporary account with balance below buffer, runs projection, asserts first breach equals horizon_start

INSERT INTO account (account_id, name, account_type, buffer_min)
VALUES (990, 'Day 1 Breach Account', 'SAVINGS', 50000.00);

INSERT INTO balance_checkpoint (account_id, as_of_date, balance)
VALUES (990, '2026-10-01', 30000.00);

CALL build_projection(1, 990, 30, @run_id_t12);

SELECT 
    run_id, 
    account_id, 
    horizon_start, 
    first_breach_date,
    (first_breach_date = horizon_start) AS is_day_one_breach
FROM projection_run 
WHERE run_id = @run_id_t12;

-- Cleanup
DELETE FROM account WHERE account_id = 990;
