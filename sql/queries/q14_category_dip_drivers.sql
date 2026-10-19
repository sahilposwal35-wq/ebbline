-- Query Q14: Which categories drive the dip before the breach?
-- Technique: GROUP BY category over the breach window
-- Parameters: @run_id, @first_breach

SELECT 
    c.category_id,
    c.name AS category_name,
    c.is_essential,
    COUNT(*) AS event_count,
    SUM(pe.amount) AS total_outflow
FROM projection_event pe
JOIN category c ON c.category_id = pe.category_id
WHERE pe.run_id = @run_id 
  AND pe.due_date <= @first_breach
GROUP BY c.category_id, c.name, c.is_essential
ORDER BY total_outflow ASC;
