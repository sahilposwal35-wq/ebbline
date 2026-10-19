-- Phase 1: Constraint Verification Tests
-- Each test below checks that invalid data is rejected by schema constraints or procedures.

-- Test C1: Account buffer minimum cannot be negative
-- Expect: ERROR (ck_account_buffer violated)
INSERT INTO account (name, account_type, buffer_min) VALUES ('Test Negative Buffer', 'SAVINGS', -100.00);

-- Test C2: Account name must be unique
-- Expect: ERROR (Duplicate entry)
INSERT INTO account (name, account_type, buffer_min) VALUES ('Salary Account', 'SAVINGS', 5000.00);
INSERT INTO account (name, account_type, buffer_min) VALUES ('Salary Account', 'CURRENT', 1000.00);

-- Test C3: Recurring rule amount cannot be zero
-- Expect: ERROR (ck_rule_amount violated)
INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date)
VALUES (1, 1, 'Zero Rule', 0.00, 'MONTH', 1, '2026-01-01');

-- Test C4: Recurring rule every_n must be at least 1
-- Expect: ERROR (ck_rule_every violated)
INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date)
VALUES (1, 1, 'Zero Frequency', 1000.00, 'MONTH', 0, '2026-01-01');

-- Test C5: Recurring rule end_date cannot precede start_date
-- Expect: ERROR (ck_rule_dates violated)
INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date, end_date)
VALUES (1, 1, 'Backwards Dates', 1000.00, 'MONTH', 1, '2026-12-01', '2026-01-01');

-- Test C6: One-off event amount cannot be zero
-- Expect: ERROR (ck_event_amount violated)
INSERT INTO one_off_event (account_id, category_id, event_date, amount, label)
VALUES (1, 1, '2026-05-01', 0.00, 'Zero Event');

-- Test C7: Scenario change must target exactly one of rule_id or event_id (both null)
-- Expect: ERROR (ck_change_target violated)
INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date)
VALUES (1, NULL, NULL, 'SKIP', NULL, '2026-01-01', '2026-01-31');

-- Test C8: Scenario change cannot target both rule_id and event_id
-- Expect: ERROR (ck_change_target violated)
INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date)
VALUES (1, 1, 1, 'SKIP', NULL, '2026-01-01', '2026-01-31');

-- Test C9: Scenario change date range must have to_date >= from_date
-- Expect: ERROR (ck_change_range violated)
INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date)
VALUES (1, 1, NULL, 'SKIP', NULL, '2026-05-01', '2026-04-01');

-- Test C10: Scenario change SCALE requires non-null value
-- Expect: ERROR (ck_change_value violated)
INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date)
VALUES (1, 1, NULL, 'SCALE', NULL, '2026-05-01', '2026-05-31');

-- Test C11: Category in use cannot be deleted (Foreign key integrity)
-- Expect: ERROR (Cannot delete or update a parent row: a foreign key constraint fails)
DELETE FROM category WHERE category_id = 1;
