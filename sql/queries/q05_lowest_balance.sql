-- Query Q5: Lowest balance and its date?
-- Technique: ORDER BY balance ASC, day ASC LIMIT 1
-- Parameters: @run_id

SELECT 
    day AS min_balance_date,
    balance AS min_balance
FROM projection_day
WHERE run_id = @run_id
ORDER BY balance ASC, day ASC
LIMIT 1;
