-- Query Q3: What is the balance each day?
-- Technique: Window function SUM() OVER with explicit ROWS frame
-- Parameters: @run_id

SELECT 
    day,
    net,
    balance
FROM projection_day
WHERE run_id = @run_id
ORDER BY day;
