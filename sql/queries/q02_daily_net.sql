-- Query Q2: What is the net per calendar day, including empty days?
-- Technique: LEFT JOIN to calendar_day, COALESCE(SUM(amount), 0)
-- Parameters: @run_id, @start_date, @end_date

SELECT 
    cd.day,
    COALESCE(SUM(pe.amount), 0.00) AS net
FROM calendar_day cd
LEFT JOIN projection_event pe ON pe.run_id = @run_id AND pe.due_date = cd.day
WHERE cd.day BETWEEN @start_date AND @end_date
GROUP BY cd.day
ORDER BY cd.day;
