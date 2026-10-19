-- Query Q6: How many days below buffer?
-- Technique: SUM(balance < buffer)
-- Parameters: @run_id, @buffer_min

SELECT COUNT(*) AS days_below_buffer
FROM projection_day
WHERE run_id = @run_id 
  AND balance < @buffer_min;
