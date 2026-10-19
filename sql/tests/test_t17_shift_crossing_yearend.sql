-- Test T17: Weekly rule with SHIFT_DAYS crossing 31 Dec
-- Shifts occurrence from late December into January of next year

INSERT INTO scenario (scenario_id, name, description)
VALUES (917, 'T17 Year End Shift', 'Testing shift crossing into next year');

-- Rule 6 occurrence on 2026-12-26 shifted by +7 days should land on 2027-01-02
INSERT INTO scenario_change (scenario_id, rule_id, action, value, from_date, to_date)
VALUES (917, 6, 'SHIFT_DAYS', 7.00, '2026-12-20', '2026-12-31');

CALL build_projection(917, 1, 120, @run_id_t17);

SELECT due_date
FROM projection_event
WHERE run_id = @run_id_t17
  AND source_type = 'RULE'
  AND source_id = 6
  AND due_date = '2027-01-02';

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 917;
