-- Query Q9: Which discretionary items fix the breach?
-- Technique: Cumulative window sum over discretionary outflows
-- Parameters: @run_id, @shortfall, @first_breach

WITH cand AS (
    SELECT 
        pe.event_id, 
        pe.due_date, 
        pe.label, 
        -pe.amount AS saving
    FROM projection_event pe
    JOIN category c ON c.category_id = pe.category_id
    WHERE pe.run_id = @run_id 
      AND c.is_essential = FALSE
      AND pe.amount < 0 
      AND pe.due_date <= @first_breach
), 
ranked AS (
    SELECT 
        cand.*,
        SUM(saving) OVER (
            ORDER BY saving DESC, due_date, event_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cum_saving
    FROM cand
)
SELECT * 
FROM ranked
WHERE cum_saving - saving < @shortfall;
