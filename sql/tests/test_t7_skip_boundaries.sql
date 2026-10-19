-- Test T7: SKIP boundaries (from_date and to_date inclusive)
-- Verifies occurrences on the exact boundary dates from_date and to_date are skipped

-- Setup temporary test scenario
INSERT INTO scenario (scenario_id, name, description)
VALUES (907, 'T7 Test Scenario', 'Testing SKIP boundary inclusiveness');

-- Target Rule 6 (Bi-weekly Groceries: Oct 03, Oct 17, Oct 31)
-- Skip with range exactly 2026-10-03 to 2026-10-31
INSERT INTO scenario_change (scenario_id, rule_id, action, from_date, to_date)
VALUES (907, 6, 'SKIP', '2026-10-03', '2026-10-31');

CALL build_projection(907, 1, 60, @run_id_t7);

-- Verify that Oct 03, Oct 17, Oct 31 occurrences are all omitted
SELECT COUNT(*) AS occ_found
FROM projection_event
WHERE run_id = @run_id_t7
  AND source_type = 'RULE'
  AND source_id = 6
  AND due_date BETWEEN '2026-10-03' AND '2026-10-31';

-- Cleanup
DELETE FROM scenario WHERE scenario_id = 907;
