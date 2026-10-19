-- Ebbline Database Indexes
-- Engine: MySQL 8.0 or later

-- 1. Index on recurring_rule for fast active rule lookup per account
CREATE INDEX idx_rule_acc_active ON recurring_rule (account_id, is_active);

-- 2. Index on one_off_event for date-range event lookup per account
CREATE INDEX idx_event_acc_date ON one_off_event (account_id, event_date);

-- 3. Composite indexes on scenario_change for fast rule/event action lookup during projection builds
CREATE INDEX idx_change_scen_rule ON scenario_change (scenario_id, rule_id, from_date, to_date);
CREATE INDEX idx_change_scen_event ON scenario_change (scenario_id, event_id, from_date, to_date);

-- 4. Indexes on actual_txn for plan vs actual matching and account filtering
CREATE INDEX idx_actual_rule_date ON actual_txn (rule_id, txn_date);
CREATE INDEX idx_actual_acc_date ON actual_txn (account_id, txn_date);

-- 5. Covering index on projection_run for latest run lookup
CREATE INDEX idx_proj_run_lookup ON projection_run (account_id, scenario_id, run_id);
