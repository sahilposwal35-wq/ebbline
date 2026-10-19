-- Test T10: Overlapping scenario changes rejected
-- Touching ranges (same start and end day) are rejected by trg_change_no_overlap with error 45005

INSERT INTO scenario (scenario_id, name, description)
VALUES (910, 'T10 Overlap Test', 'Testing trigger overlap rejection');

-- First change: Oct 01 to Oct 15
INSERT INTO scenario_change (scenario_id, rule_id, action, from_date, to_date)
VALUES (910, 1, 'SKIP', '2026-10-01', '2026-10-15');

-- Second change touching Oct 15 (Oct 15 to Oct 31): should be rejected with error 45005
INSERT INTO scenario_change (scenario_id, rule_id, action, from_date, to_date)
VALUES (910, 1, 'SKIP', '2026-10-15', '2026-10-31');

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 910;
