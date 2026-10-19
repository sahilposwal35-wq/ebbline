-- Ebbline Database Views
-- Engine: MySQL 8.0 or later

-- View 1: v_rule_occurrence
-- Purpose: Expands every active recurring rule into dated occurrences over a 10-year horizon.
-- Uses recursive CTEs for monthly and weekly rules.
CREATE OR REPLACE VIEW v_rule_occurrence AS
WITH RECURSIVE seq_month AS (
    SELECT 0 AS k
    UNION ALL
    SELECT k + 1 FROM seq_month WHERE k < 120
),
seq_week AS (
    SELECT 0 AS k
    UNION ALL
    SELECT k + 1 FROM seq_week WHERE k < 520
)
SELECT 
    'RULE' AS source_type,
    r.rule_id AS source_id,
    r.account_id,
    r.category_id,
    r.label,
    r.amount,
    r.start_date,
    r.end_date,
    DATE_ADD(r.start_date, INTERVAL (m.k * r.every_n) MONTH) AS due_date
FROM recurring_rule r
JOIN seq_month m
WHERE r.is_active = TRUE
  AND r.unit = 'MONTH'
  AND DATE_ADD(r.start_date, INTERVAL (m.k * r.every_n) MONTH) <= COALESCE(r.end_date, '2035-12-31')

UNION ALL

SELECT 
    'RULE' AS source_type,
    r.rule_id AS source_id,
    r.account_id,
    r.category_id,
    r.label,
    r.amount,
    r.start_date,
    r.end_date,
    DATE_ADD(r.start_date, INTERVAL (w.k * r.every_n) WEEK) AS due_date
FROM recurring_rule r
JOIN seq_week w
WHERE r.is_active = TRUE
  AND r.unit = 'WEEK'
  AND DATE_ADD(r.start_date, INTERVAL (w.k * r.every_n) WEEK) <= COALESCE(r.end_date, '2035-12-31');

-- View 2: v_latest_run
-- Purpose: Finds the most recent projection run for each account and scenario combination.
CREATE OR REPLACE VIEW v_latest_run AS
SELECT pr.*
FROM projection_run pr
JOIN (
    SELECT account_id, scenario_id, MAX(run_id) AS max_run_id
    FROM projection_run
    GROUP BY account_id, scenario_id
) latest ON pr.run_id = latest.max_run_id;

-- View 3: v_scenario_diff
-- Purpose: Compares the baseline run against other scenario runs for the same account.
CREATE OR REPLACE VIEW v_scenario_diff AS
SELECT 
    base.account_id,
    alt.scenario_id AS scenario_b_id,
    alt.run_id AS run_b_id,
    base.run_id AS run_baseline_id,
    base.min_balance AS baseline_min_balance,
    alt.min_balance AS scenario_b_min_balance,
    (alt.min_balance - base.min_balance) AS min_balance_delta,
    base.first_breach_date AS baseline_breach_date,
    alt.first_breach_date AS scenario_b_breach_date,
    DATEDIFF(alt.first_breach_date, base.first_breach_date) AS breach_date_shift_days,
    base.days_below_buffer AS baseline_days_below,
    alt.days_below_buffer AS scenario_b_days_below,
    (alt.days_below_buffer - base.days_below_buffer) AS days_below_buffer_delta
FROM v_latest_run base
JOIN v_latest_run alt ON base.account_id = alt.account_id AND base.scenario_id = 1 AND alt.scenario_id <> 1;

-- View 4: v_plan_vs_actual
-- Purpose: Compares planned rule amounts against posted actual amounts per month with a 3-month rolling average.
CREATE OR REPLACE VIEW v_plan_vs_actual AS
WITH monthly_data AS (
    SELECT 
        r.rule_id,
        r.account_id,
        r.label AS rule_label,
        r.amount AS planned_amount,
        DATE_FORMAT(cd.day, '%Y-%m') AS ym,
        COALESCE(SUM(a.amount), 0.00) AS actual_amount
    FROM recurring_rule r
    JOIN calendar_day cd ON cd.day >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND cd.day <= CURDATE()
    LEFT JOIN actual_txn a ON a.rule_id = r.rule_id AND DATE_FORMAT(a.txn_date, '%Y-%m') = DATE_FORMAT(cd.day, '%Y-%m')
    WHERE r.is_active = TRUE
    GROUP BY r.rule_id, r.account_id, r.label, r.amount, ym
)
SELECT 
    rule_id,
    account_id,
    rule_label,
    ym,
    planned_amount,
    actual_amount,
    (actual_amount - planned_amount) AS variance,
    CASE 
        WHEN planned_amount <> 0 THEN ROUND(((actual_amount - planned_amount) / ABS(planned_amount)) * 100.0, 2)
        ELSE 0.00 
    END AS variance_pct,
    ROUND(AVG(actual_amount) OVER (
        PARTITION BY rule_id 
        ORDER BY ym 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS avg_3m
FROM monthly_data;

-- View 5: v_reserve_schedule
-- Purpose: Calculates monthly reserve set-aside for quarterly and yearly obligations.
CREATE OR REPLACE VIEW v_reserve_schedule AS
SELECT 
    r.rule_id,
    r.account_id,
    r.label,
    r.amount AS total_obligation,
    r.unit,
    r.every_n,
    CASE 
        WHEN r.unit = 'MONTH' THEN r.every_n
        WHEN r.unit = 'WEEK' THEN ROUND((r.every_n * 7.0) / 30.4375, 2)
        ELSE 1
    END AS period_months,
    ROUND(ABS(r.amount) / CASE 
        WHEN r.unit = 'MONTH' THEN r.every_n
        WHEN r.unit = 'WEEK' THEN ROUND((r.every_n * 7.0) / 30.4375, 2)
        ELSE 1
    END, 2) AS monthly_set_aside
FROM recurring_rule r
WHERE r.is_active = TRUE 
  AND r.amount < 0
  AND ((r.unit = 'MONTH' AND r.every_n >= 3) OR (r.unit = 'WEEK' AND r.every_n >= 12));
