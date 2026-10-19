-- Test T19: SCALE 1.5 on an outflow
-- Rent of -30000.00 scaled by 1.50 becomes -45000.00 (Decision D9)

INSERT INTO scenario (scenario_id, name, description)
VALUES (919, 'T19 Scale Outflow', 'Testing 1.5x scale on outflow');

INSERT INTO scenario_change (scenario_id, rule_id, action, value, from_date, to_date)
VALUES (919, 2, 'SCALE', 1.50, '2026-10-01', '2026-10-31');

CALL build_projection(919, 1, 60, @run_id_t19);

SELECT amount
FROM projection_event
WHERE run_id = @run_id_t19
  AND source_type = 'RULE'
  AND source_id = 2
  AND due_date = '2026-10-05';

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 919;
