-- Test T16: Hand-calculated 3-month case matches SQL result to the paisa.
-- Runs projection for 90 days on Account 1, baseline scenario.

CALL build_projection(1, 1, 90, @run_id_t16);

SELECT 
    day, 
    net, 
    balance
FROM projection_day 
WHERE run_id = @run_id_t16 
ORDER BY day;
