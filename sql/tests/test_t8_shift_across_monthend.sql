-- Test T8: SHIFT across month end
-- Verifies date shifted by +5 days correctly rolls into the next month

INSERT INTO scenario (scenario_id, name, description)
VALUES (908, 'T8 Shift Test', 'Testing month end shift');

-- Target Rule 9 (Society Maintenance Month-End: Oct 31)
-- Shift +5 days: 2026-10-31 + 5 days = 2026-11-05
INSERT INTO scenario_change (scenario_id, rule_id, action, value, from_date, to_date)
VALUES (908, 9, 'SHIFT_DAYS', 5.00, '2026-10-01', '2026-10-31');

CALL build_projection(908, 1, 60, @run_id_t8);

SELECT due_date
FROM projection_event
WHERE run_id = @run_id_t8
  AND source_type = 'RULE'
  AND source_id = 9
  AND due_date BETWEEN '2026-11-01' AND '2026-11-10';

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 908;
