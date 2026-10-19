-- Query Q4: First day below buffer?
-- Technique: MIN(day) with filter condition
-- Parameters: @run_id, @buffer_min

SELECT MIN(day) AS first_breach_date
FROM projection_day
WHERE run_id = @run_id 
  AND balance < @buffer_min;
