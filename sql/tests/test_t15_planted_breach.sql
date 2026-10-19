-- Test T15: Planted breach date matches exactly
-- Account 1 is engineered to breach on exactly 2026-10-18.

CALL build_projection(1, 1, 365, @run_id_t15);

SELECT 
    run_id, 
    account_id, 
    first_breach_date,
    (first_breach_date = '2026-10-18') AS matches_planted_breach
FROM projection_run 
WHERE run_id = @run_id_t15;
