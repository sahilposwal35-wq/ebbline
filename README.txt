Ebbline Cash Flow Forecasting Engine

1. Overview
Ebbline is a forward looking cash flow forecasting engine for personal finance built on MySQL 8 and Python with Streamlit. The application models recurring obligations such as rent, loan instalments, investments, insurance premiums and subscriptions alongside one time events. The database expands recurring patterns across time horizons up to 730 days, projects daily account balances with explicit running window functions, flags the exact day an account dips below its safety buffer, explains the driving transactions behind any dip, and suggests actionable discretionary adjustments across what if scenarios. All business logic, constraints, running balance arithmetic, triggers, and analytical procedures live strictly in MySQL. Python and Streamlit serve only as a thin presentation and orchestration layer.

2. Technology Stack and Requirements
Database: MySQL 8.0 or later (verified on MySQL 8.4 LTS).
Runtime: Python 3.11 or later.
Dependencies: mysql-connector-python, streamlit, altair, pandas.
Operating System: Linux, macOS, or Windows.

3. Quickstart and Setup Instructions
Step 1. Configure environment file.
Copy the example environment configuration:
cp .env.example .env
Edit .env to set your MySQL host, port, database name, user, password, and optional unix socket path.

Step 2. Create the database and user.
Log into your MySQL server as administrator and execute:
CREATE DATABASE IF NOT EXISTS ebbline;
CREATE USER IF NOT EXISTS 'ebbline'@'localhost' IDENTIFIED BY 'ebbline_password';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON ebbline.* TO 'ebbline'@'localhost';
FLUSH PRIVILEGES;

Step 3. Initialize schema, views, procedures, triggers, and indexes.
Run the database initialization command using the command line interface:
python app/cli.py init-db
Alternatively, apply the SQL files in order from the repository root:
mysql -u root ebbline < sql/00_schema.sql
mysql -u root ebbline < sql/01_views.sql
mysql -u root ebbline < sql/02_procedures.sql
mysql -u root ebbline < sql/03_triggers.sql
mysql -u root ebbline < sql/04_indexes.sql

Step 4. Seed synthetic data.
Generate the standard synthetic dataset with fixed seed 42:
python app/cli.py seed
This populates calendar days, core categories, baseline accounts, and all ten planted test cases.

Step 5. Run the automated test suite.
Execute all 51 tests across constraints, expansions, projections, scenarios, analytics, and invariants:
python tests/run_tests.py

Step 6. Launch the web interface.
Start the Streamlit application:
streamlit run app/ui.py
Open your web browser at http://localhost:8501 to access the five screens.

4. Data Model and Relational Architecture
The database schema consists of thirteen tables designed in third normal form with strict referential constraints:
account: Stores bank accounts with non-negative safety buffer thresholds.
balance_checkpoint: Records verified real balances on specific anchor dates.
category: Groups transactions with an essential or discretionary classification.
recurring_rule: Defines income and expense rules with weekly or monthly intervals and every n multiplier.
one_off_event: Records single date financial events.
scenario: Stores what if scenario headers, beginning with scenario 1 as the immutable Baseline.
scenario_change: Stores overrides (skip, shift days, scale) targeted to a rule or event.
actual_txn: Stores posted transactions with SHA-256 hash deduplication.
projection_run: Append only header storing projection parameters, lowest balance, and breach metrics.
projection_day: Daily ledger of net transactions and calculated running balance.
projection_event: Expanded occurrences belonging to a projection run.
rule_history: Audit table logging changes to recurring rules populated by trigger.
calendar_day: Prepopulated calendar dimension covering multi-year projection spans.

5. Database Logic and SQL Objects
Views:
v_rule_occurrence: Expands active rules using recursive CTEs for monthly and weekly schedules without end of month drift.
v_latest_run: Resolves the most recent projection run per account and scenario.
v_scenario_diff: Calculates deltas in minimum balance, breach date, and days below buffer between Baseline and alternative scenarios.
v_plan_vs_actual: Computes monthly variances and three month rolling averages between rules and posted actuals.
v_reserve_schedule: Computes monthly set-aside amounts required for quarterly and annual obligations.

Stored Procedures:
add_checkpoint: Inserts verified checkpoint balances with validation rejecting future dates.
build_projection: Runs in an atomic transaction to expand occurrences, apply scenario overrides, compute daily nets, calculate running balances via window functions, evaluate safety buffer breaches, and commit run records.
add_scenario_change: Locks the parent scenario with SELECT FOR UPDATE and validates date ranges before inserting changes.
compare_scenarios: Compares two scenarios for an account, generating projection runs on demand if needed.
explain_day: Returns day summaries, individual events ordered by largest outflow first, and category dip drivers.
suggest_fixes: Identifies the fewest discretionary outflows before the first breach that cover the shortfall.
backtest: Compares earlier projection runs against subsequent balance checkpoints, calculating mean absolute error and root mean square error.

Triggers:
trg_change_no_overlap_insert: Rejects overlapping date ranges for the same rule or event in a scenario.
trg_change_no_overlap_update: Enforces overlap protection during scenario change updates.
trg_baseline_immutability_insert: Blocks inserting scenario changes against scenario 1 Baseline.
trg_rule_history: Logs prior and new amounts, dates, and active flags whenever a recurring rule is modified.

6. Planted Test Cases
The synthetic seed generator incorporates ten planted validation cases:
P1: Monthly rule starting 31 January testing month end clamping on 28 February and restoration on 31 March.
P2: Monthly rule starting 29 February of a leap year verifying non leap year handling.
P3: Weekly rule with every n equals 2 verifying exact fourteen day spacing.
P4: Yearly obligation with unit MONTH and every n equals 12 verifying annual reserve calculation.
P5: Primary account engineered to breach its safety buffer on 18 October 2026.
P6: Secondary account engineered to maintain balance comfortably above buffer across all 365 days.
P7: Rule with no postings in three months to test stale rule detection.
P8: Rules whose actual postings deviate by five to fifteen percent from planned values.
P9: Account with multiple balance checkpoints to validate forecast backtesting.
P10: Discretionary subscription outflow scheduled before the planted breach date to test fix suggestions.

All data in Ebbline is entirely synthetic. No real financial data or personal credentials are used or stored.

7. Benchmark Measurements
Performance was measured on native MySQL 8.4 on Linux x86_64 with 12 CPU cores and 14.8 GB RAM:
build_projection 365 days: 26.79 milliseconds median on seed data, 24.68 milliseconds on stress dataset with over 1000 rules.
build_projection 730 days: 37.86 milliseconds median on seed data, 33.79 milliseconds on stress dataset.
compare_scenarios: 2.52 milliseconds median on seed data.
explain_day: 3.42 milliseconds median on seed data.
backtest: 2.34 milliseconds median on seed data.
Full details and EXPLAIN ANALYZE execution plans before and after indexing are recorded in docs/benchmarks.txt.

8. Known Limits and Design Boundaries
First, recurrence expansion via recursive CTEs is capped at 120 iterations for monthly rules and 520 for weekly rules to ensure queries remain well below the MySQL default recursion limit of 1000.
Second, MySQL check constraints do not support non-deterministic functions such as CURDATE, so future date guards are enforced inside stored procedures.
Third, fix suggestions address the first breach date only, as resolving early breaches frequently alters cash flow dynamics for subsequent periods.
Fourth, forecast backtest figures computed on synthetic seed data verify algorithmic accuracy and procedure mechanics but do not reflect real world human spending volatility.
