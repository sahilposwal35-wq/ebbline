-- Test T9: SCALE by 0
-- Verifies multiplying amount by 0.00 yields 0.00 amount

INSERT INTO scenario (scenario_id, name, description)
VALUES (909, 'T9 Scale Zero Test', 'Testing scale factor 0.00');

INSERT INTO scenario_change (scenario_id, rule_id, action, value, from_date, to_date)
VALUES (909, 2, 'SCALE', 0.00, '2026-10-01', '2026-10-31');

CALL build_projection(909, 1, 60, @run_id_t9);

SELECT amount
FROM projection_event
WHERE run_id = @run_id_t9
  AND source_type = 'RULE'
  AND source_id = 2
  AND due_date = '2026-10-05';

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 909;
