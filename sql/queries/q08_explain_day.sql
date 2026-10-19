-- Query Q8: What made up this day's balance?
-- Technique: Running SUM() OVER over projection_event
-- Parameters: @run_id, @day

SELECT 
    pe.event_id,
    pe.due_date,
    pe.source_type,
    pe.source_id,
    pe.label,
    pe.amount,
    pr.anchor_balance + SUM(pe.amount) OVER (
        ORDER BY pe.due_date, pe.amount ASC, pe.event_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance
FROM projection_event pe
JOIN projection_run pr ON pr.run_id = pe.run_id
WHERE pe.run_id = @run_id 
  AND pe.due_date <= @day
ORDER BY pe.due_date, pe.amount ASC, pe.event_id;
