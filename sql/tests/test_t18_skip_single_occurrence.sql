-- Test T18: SKIP range covering exactly one occurrence
-- Only that single occurrence is removed; prior and subsequent occurrences remain

INSERT INTO scenario (scenario_id, name, description)
VALUES (918, 'T18 Single Skip Test', 'Testing single occurrence skip');

-- Rule 6 has occurrences Oct 03, Oct 17, Oct 31.
-- Skip range covering only Oct 17: '2026-10-10' to '2026-10-20'
INSERT INTO scenario_change (scenario_id, rule_id, action, from_date, to_date)
VALUES (918, 6, 'SKIP', '2026-10-10', '2026-10-20');

CALL build_projection(918, 1, 60, @run_id_t18);

-- Oct 03 and Oct 31 should exist, Oct 17 should be missing
SELECT due_date
FROM projection_event
WHERE run_id = @run_id_t18
  AND source_type = 'RULE'
  AND source_id = 6
  AND due_date BETWEEN '2026-10-01' AND '2026-10-31'
ORDER BY due_date;

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 918;
