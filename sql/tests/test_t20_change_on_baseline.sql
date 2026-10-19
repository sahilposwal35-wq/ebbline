-- Test T20: Insert a change on Baseline scenario
-- Expected: Rejected with error 45006

INSERT INTO scenario_change (scenario_id, rule_id, action, from_date, to_date)
VALUES (1, 1, 'SKIP', '2026-10-01', '2026-10-31');
