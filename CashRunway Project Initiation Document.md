# Ebbline: Project Initiation Document

*Version 2.0 (final) · 19 October 2026 · Author: \[Your name\] · Status: ready for build*

## 1. Executive Summary

Ebbline is a MySQL 8 cash-flow forecasting engine for personal finance. Most personal finance tools look backward and show what was spent. Ebbline looks forward. It expands a person's recurring obligations (rent, EMI, SIP, insurance, annual fees) into dated events, projects the balance for every day of the next 12 months, and reports the first date the balance falls below a chosen safety buffer. It then lets the user test changes (skip, shift or scale an obligation) as stored scenarios and compares outcomes.

**60-second pitch:** "Monthly totals hide bad weeks. I built a MySQL engine that turns recurring rules into a day-by-day projected balance, finds the first date it drops below a buffer, explains which events caused the dip, and compares what-if scenarios. The core is SQL: recursive expansion, window functions, constraints, a trigger, and transactional procedures."

The project is a database-first portfolio piece. The application layer is deliberately thin. All data is synthetic.

## 2. Background and Context

Personal cash flow is lumpy. Rent, loan EMIs and SIPs fall on fixed days. Insurance premiums, annual subscriptions and tax payments arrive quarterly or yearly. In India, UPI makes small spending frictionless, so people often lose sight of when large fixed outflows land relative to salary credits. A balance can look healthy on the 1st and be negative on the 24th.

Monthly budgets answer "how much", not "when". The gap Ebbline targets is **timing**.

## 3. Problem Statement

**Core problem.** People cannot easily see on which future date their account balance will fall below a safe level, why, and what change would prevent it.

**Sub-problems**

- **P1: Timing blindness.** Monthly totals hide intra-month dips.
- **P2: Lumpy obligations.** Quarterly and yearly payments surprise people because they are not visible in monthly views.
- **P3: No safe experimentation.** Testing "what if I skip this SIP for two months?" on real data is awkward in spreadsheets and changes the base plan.
- **P4: Unexplained numbers.** A forecast that says "you will run short" without naming the causing events is not actionable.
- **P5: Plan drift.** Planned amounts differ from actual amounts, and nobody measures how reliable the forecast is.
- **P6: Privacy friction.** Auto-tracking apps often need SMS or bank access. Some users avoid that.

**Who is affected.** Salaried young professionals with fixed obligations, and anyone with several recurring outflows on different dates.

**Impact.** Overdrafts, missed payments, forced withdrawals from savings.

## 4. Objectives and Success Criteria

**Product objectives**

- O1: Project daily balance for a chosen horizon (default 365 days) from stored rules.
- O2: Detect the first breach of the buffer and the lowest balance with its date.
- O3: Support stored scenarios and compare them.
- O4: Explain any day's balance and suggest which discretionary items to skip.

**Learning and portfolio objectives**

- O5: Demonstrate relational design, recursive CTEs, window functions, triggers, procedures, transactions and indexing, each with a real reason.
- O6: Produce a reproducible repository and a document I can defend in an interview.

**Success criteria (all verifiable)**

| ID | Criterion | How verified |
| --- | --- | --- |
| SC1 | All test cases in Section 14 pass | Automated SQL test script |
| SC2 | Projection build for 3 years on the seed data meets a target of 2 seconds or less | Measured; actual value recorded. If missed, optimise or restate the target |
| SC3 | Fresh clone builds the database and runs the demo with one script | Tested on a clean machine or container |
| SC4 | Market comparison matrix completed for at least 5 existing apps and dated | Section 5.5 |
| SC5 | I can explain the design in 60 seconds and answer the questions in Section 19 | Mock interview with a peer |

## 5. Market Landscape and Uniqueness

### 5.1 What existing tools do

From public roundups of Indian personal finance apps (October 2026), typical offerings are:

- **SMS-parsing auto-trackers** (for example Walnut): read bank and payment SMS alerts to log and categorise spending.
- **All-in-one dashboards** (for example INDmoney): auto-categorisation, net worth, mutual fund and EPF tracking, subscription detection.
- **Shared and couples tracking** (for example Spendee).
- **Manual or privacy-first trackers** (for example Monefy, Pocket Clear): no bank link or SMS permission.
- **Consent-based data sharing** through the RBI Account Aggregator framework in some apps.

This list is from secondary sources and is not exhaustive. Phase 0 verifies it first-hand.

### 5.2 The gap

The listed tools centre on recording and categorising past spending, net worth and savings. The reviewed sources did not emphasise a user-controlled, scenario-based daily balance forecast with explained breach dates. Some global apps include forecasting features, so I will not claim that no tool does this. I claim a specific combination, verified through the matrix in 5.5.

### 5.3 Differentiators

| ID | Differentiator | Why it matters |
| --- | --- | --- |
| U1 | **Forward-looking runway engine.** Output is a dated balance curve and a breach date, not a spending report | Answers "when", not "how much" |
| U2 | **Scenarios stored as data.** Skip, shift or scale a rule over a date range without touching the base plan | Safe experimentation, diffable results |
| U3 | **Explainable breaches.** Lists the events that drove the balance down before the breach date | Forecast becomes actionable |
| U4 | **Fix suggestions.** Ranks discretionary obligations and uses a cumulative window to find the smallest set that covers the shortfall | Turns a warning into a decision |
| U5 | **Zero-permission input.** Manual entry and CSV import, no SMS, no bank link | Privacy by design |
| U6 | **Self-auditing forecast.** Backtests projections against actual balance checkpoints and reports error | Honest reliability measure |
| U7 | **Lumpy-obligation reserve schedule.** Computes the monthly amount to set aside for yearly and quarterly items | Removes the surprise in P2 |
| U8 | **Fully traceable numbers.** Every projected balance can be rebuilt from stored rows | Trust and testability |

### 5.4 Honest limits

- It does not auto-import transactions, categorise spending, track investments or net worth, or move money.
- Forecast quality depends on the user's rules being right.
- Irregular income (freelancers) is handled only through one-off events and scenarios, not prediction.

### 5.5 Market validation protocol (Phase 0)

Build a dated matrix of at least 5 apps (include 2 global apps with forecasting). Columns: daily balance forecast, breach date alert, what-if scenarios, explanation of cause, fix suggestion, input method, permissions needed, free or paid. Fill it from trial use or official documentation, with the date. Revise U1 to U8 if a row shows an existing tool already does it well. Only then write the uniqueness claim.

### 5.6 Positioning statement

For people with several recurring obligations who want to avoid running short, Ebbline is a privacy-first, SQL-driven runway forecaster. Unlike spending trackers, it predicts when the balance dips, explains why, and tests fixes safely.

## 6. Brainstorming Log

### 6.1 Ideas considered for the whole project

| Idea | Decision | Reason |
| --- | --- | --- |
| Plain expense tracker | Rejected | Saturated category; weak SQL depth |
| Bank or ledger system | Rejected | Excluded by requirements; overused |
| AccessLens (access recertification) | Alternative | Strong SQL, less personal; kept as backup |
| LineageGraph (data lineage) | Alternative | Recursion-heavy, narrower story |
| **Ebbline** | **Selected** | Clear problem, forward-looking, SQL is the engine, easy to explain |

### 6.2 Feature brainstorm, raw list

Budget envelopes, bill reminders, SMS import, receipt OCR, category pie charts, net worth, goal tracking, split bills, credit score, investment tracking, daily balance projection, breach date, scenarios, explain-day, fix suggestions, reserve schedule, backtest, CSV import, weekend date adjustment, multi-currency, income prediction.

### 6.3 Filter result

- **Kept:** the forecasting and analysis items.
- **Cut as market-common or off-core:** envelopes, reminders, SMS import, OCR, charts-as-product, net worth, goals, split bills, credit score, investments.
- **Deferred:** multi-currency, income prediction, weekend date adjustment.

## 7. Scope

**In scope:** accounts, balance checkpoints, recurring rules, one-off events, categories with an essential flag, projection, breach detection, scenarios and comparison, explain-day, fix suggestions, plan-vs-actual variance, backtest, reserve schedule, CSV import of actual transactions, thin UI, synthetic data, tests, documentation.

**Out of scope:** authentication and multi-user, bank or SMS integration, mobile app, investments, tax calculation, notifications, machine-learning prediction, real financial data.

## 8. Users and Use Cases

**Primary persona:** salaried professional with rent, EMI, SIP, insurance and subscriptions on different dates. **Secondary persona:** freelancer with uneven income, who uses one-off events.

**User stories**

1. As a user, I enter recurring rules so the system knows my obligations.
2. As a user, I record my current balance so projections start from reality.
3. As a user, I see my balance for each future day so I can spot dips.
4. As a user, I see the first date I go below my buffer.
5. As a user, I see which events caused the dip.
6. As a user, I test skipping or shifting an item without changing my real plan.
7. As a user, I compare scenarios side by side.
8. As a user, I see how much to reserve monthly for yearly bills.
9. As a user, I see how accurate past forecasts were.

## 9. Feature List

| ID | Feature | Priority | Phase |
| --- | --- | --- | --- |
| F1 | Account management with per-account buffer | Must | 1 |
| F2 | Balance checkpoints (known balance on a date) | Must | 1 |
| F3 | Recurring rules: weekly or monthly, every N units, start and end dates | Must | 3 |
| F4 | One-off events | Must | 3 |
| F5 | Categories with essential or discretionary flag | Must | 1 |
| F6 | Occurrence expansion over a horizon | Must | 3 |
| F7 | Daily projected balance | Must | 4 |
| F8 | Breach detection and lowest balance with date | Must | 4 |
| F9 | Scenarios: SKIP, SHIFT\_DAYS, SCALE | Must | 5 |
| F10 | Overlap protection for scenario changes | Must | 5 |
| F11 | Scenario comparison | Must | 5 |
| F12 | Explain-day report | Should | 6 |
| F13 | Fix suggestions | Should | 6 |
| F14 | Plan vs actual variance | Should | 6 |
| F15 | Forecast backtest | Should | 6 |
| F16 | Reserve schedule for yearly and quarterly items | Should | 6 |
| F17 | CSV import of actual transactions | Should | 6 |
| F18 | Rule change history by trigger | Could | 7 |
| F19 | Thin UI (Streamlit or CLI) | Must | 8 |
| F20 | Report export (CSV or Markdown) | Could | 8 |
| F21 | Synthetic data generator | Must | 2 |
| F22 | Automated tests | Must | 7 |

## 10. Solution Design

### 10.1 Architecture

Three layers. **MySQL** holds data and all business logic (views, procedures, trigger). A **Python script layer** seeds data, imports CSV and calls procedures. A **thin UI** (Streamlit or CLI) displays results. No logic duplicates between Python and SQL; Python only calls SQL.

### 10.2 Data model

| Table | Key columns | Purpose |
| --- | --- | --- |
| `account` | account\_id, name, account\_type, buffer\_min | A cash source |
| `balance_checkpoint` | account\_id, as\_of\_date, balance | Known real balance; projections start from the latest |
| `category` | category\_id, name, is\_essential | Essential vs discretionary |
| `recurring_rule` | rule\_id, account\_id, category\_id, label, amount (signed), unit, every\_n, start\_date, end\_date, is\_active | Obligations and income |
| `one_off_event` | event\_id, account\_id, category\_id, event\_date, amount, label | Single events |
| `scenario` | scenario\_id, name, description | Baseline is scenario 1 with no changes |
| `scenario_change` | change\_id, scenario\_id, rule\_id or event\_id, action, value, from\_date, to\_date | What-if overrides |
| `actual_txn` | txn\_id, account\_id, txn\_date, amount, rule\_id, event\_id | Real postings for variance |
| `projection_run` | run\_id, scenario\_id, account\_id, horizon\_start, horizon\_end, created\_at, min\_balance, min\_balance\_date, first\_breach\_date | Run header |
| `projection_day` | run\_id, day, balance | Daily result, primary key (run\_id, day) |
| `rule_history` (Could) | history\_id, rule\_id, changed\_at, old and new values | Trigger-fed audit |

Relationships: account 1-N rule, event, checkpoint, txn; category 1-N rule and event; scenario 1-N change; change N-1 rule or event; run 1-N day.

Money is `DECIMAL(12,2)`, never `FLOAT`. Quarterly and yearly rules use `unit = MONTH` with `every_n = 3` or `12`.

### 10.3 Business rules

- BR1: Amount is signed and non-zero. Income positive, spend negative.
- BR2: `end_date` is null or not before `start_date`.
- BR3: A monthly occurrence is `start_date + k × every_n months`, computed from the start date, not from the previous occurrence. This prevents drift after month-end clamping (31 Jan to 28 Feb stays 31 Mar).
- BR4: A projection starts from the latest checkpoint on or before the horizon start.
- BR5: A scenario change targets exactly one of a rule or an event.
- BR6: Two changes in the same scenario cannot overlap in dates on the same target.
- BR7: `SKIP` removes occurrences in range. `SHIFT_DAYS` moves them. `SCALE` multiplies the amount.
- BR8: Inactive rules produce no occurrences.
- BR9: Runs are append-only. The latest run per scenario and account is found by a view.
- BR10: Breach means balance strictly less than `buffer_min`.

### 10.4 Algorithms

1. **Expansion.** Generate integers 0..N with a recursive CTE. Join to active rules. Compute each due date with `DATE_ADD`. Filter to the horizon and the rule's end date. Add one-off events by `UNION ALL`.
2. **Scenario application.** Left join to `scenario_change` on target and date range. Drop skipped rows, shift dates, scale amounts.
3. **Daily net.** Group by day. Join to a calendar series so days with no events appear.
4. **Running balance.** Starting balance plus `SUM(net) OVER (ORDER BY day)`.
5. **Breach.** Minimum day where balance is below the buffer. Lowest balance by `ORDER BY balance LIMIT 1`.
6. **Explain-day.** List events from the previous breach window with running contribution, largest outflows first.
7. **Fix suggestions.** Among discretionary outflows before the breach date, rank by size and compute a cumulative sum with a window function. Stop when the shortfall is covered.
8. **Variance.** Join planned occurrences to `actual_txn` per rule and month. Compare to a 3-month average with `AVG() OVER`.
9. **Backtest.** For each past checkpoint, compare the earlier projection with the real balance and report absolute error.
10. **Reserve schedule.** For each yearly or quarterly rule, amount divided by months in its period, cumulatively summed by month.

### 10.5 SQL feature map, with reasons

| Feature | Reason it exists |
| --- | --- |
| Recursive CTE | Generates date offsets and occurrences without a stored calendar of occurrences |
| Window functions | Running balance, cumulative fix suggestions, rolling averages |
| `CHECK`, FK, `UNIQUE` | Enforce money and date rules in the database |
| Trigger on `scenario_change` | MySQL has no exclusion constraint, so overlap rejection needs a trigger (BR6) |
| Stored procedure `build_projection` | One atomic entry point that applies a scenario and writes a run |
| Transaction | A run header and its days are saved together or not at all |
| Views | Latest run, baseline occurrences, scenario diff |
| Indexes and `EXPLAIN ANALYZE` | Keep projection and comparison queries fast; evidence collected by measurement |
| Optional trigger on `recurring_rule` | Rule history, only if time allows |

### 10.6 Transactions and concurrency

`build_projection` runs in one transaction under InnoDB's default REPEATABLE READ so edits to rules mid-run do not mix old and new rows in one projection. Runs are append-only, so concurrent builds create separate runs instead of overwriting. The overlap trigger can race under concurrent inserts. The mitigation is to lock the parent `scenario` row (`SELECT ... FOR UPDATE`) inside the procedure that inserts changes, and to test two simultaneous sessions.

### 10.7 Indexing and performance plan

Candidate indexes: `recurring_rule(account_id, is_active)`, `one_off_event(account_id, event_date)`, `scenario_change(scenario_id, rule_id, from_date, to_date)`, `actual_txn(rule_id, txn_date)`. Method: record MySQL version and hardware, run each query 5 times, take the median, capture `EXPLAIN ANALYZE` before and after each index, and report only what was measured.

### 10.8 Security and privacy

Parameterised queries only. A least-privilege database user for the app. Credentials in a git-ignored `.env`. No real financial data in the repository. No bank credentials ever.

## 11. Technology Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Database | MySQL 8.0 or later | Required features: CTEs, window functions, CHECK enforced |
| Why not MongoDB | Rejected | Needs joins, constraints and set-based analytics |
| Scripts | Python 3.11+ with `mysql-connector-python` or PyMySQL | Seeding, CSV import, calling procedures |
| UI | Streamlit or a CLI | Minimal effort, shows the results |
| Tests | SQL test script run from Python (`pytest` optional) | Repeatable checks |
| Tools | MySQL Workbench (ER diagram), Git and GitHub | Design and versioning |
| Optional | Docker Compose with `mysql:8.0` | One-command reproducible setup |

## 12. Application Layer

Minimum screens: (1) rules and events list, (2) projection chart with breach marker, (3) scenario comparison table, (4) explain-day and fix suggestion panel, (5) reserve schedule. Everything else stays out.

## 13. Data Plan

All data is synthetic and labelled as such. Seed: about 3 accounts, 30 to 60 rules across all frequencies, 20 to 40 one-off events, 12 months of actual transactions with deliberate deviations from plan, 5 to 10 scenarios. Plant known outcomes (a guaranteed breach date, a guaranteed no-breach account, a month-end rule) so tests can assert exact results. Use a fixed random seed.

## 14. Testing and Validation

| ID | Case | Expected |
| --- | --- | --- |
| T1 | Monthly rule starting 31 Jan | Feb 28 or 29, then 31 Mar, no drift |
| T2 | Leap-year 29 Feb start | Correct clamp in non-leap years |
| T3 | Weekly rule, every 2 weeks | 14-day spacing |
| T4 | Yearly via `every_n = 12` | One occurrence per year |
| T5 | Rule ends before horizon | No occurrences after end date |
| T6 | Rule starts after horizon | No occurrences |
| T7 | SKIP boundaries | From and to dates inclusive |
| T8 | SHIFT across month end | Correct date |
| T9 | SCALE by 0 | Zero amount; confirm intended behaviour and document it |
| T10 | Overlapping scenario changes | Rejected with a clear error |
| T11 | No rules | Flat balance, no breach |
| T12 | Breach on day 1 | First breach equals horizon start |
| T13 | Multiple accounts | Results independent |
| T14 | Two concurrent builds | Two separate, consistent runs |
| T15 | Planted breach | Matches the planted date exactly |
| T16 | Hand-calculated 3-month case | Matches the SQL result to the paisa |

Performance is measured per Section 10.7. No performance claim goes into any document until measured.

## 15. Project Plan

Total: 14 days (one working buffer day included). Adjust if less time is available. The 10-day core is Phases 0 to 7.

| Phase | Day | Tasks | Deliverable | Exit check |
| --- | --- | --- | --- | --- |
| 0 Setup and validation | 1 | Install MySQL 8, repo, README skeleton; trial 5 apps; fill matrix | Market matrix, repo | SC4 draft done |
| 1 Schema | 2 | ER diagram, DDL, constraints, categories | `schema.sql` | Constraint tests reject bad rows |
| 2 Seed data | 3 | Generator with fixed seed; planted cases | `seed.py` | Counts and planted cases verified |
| 3 Expansion | 4–5 | Recursive CTE, month-end logic, events union, tests T1–T6 | `v_occurrence` | T1–T6 pass |
| 4 Projection | 6 | Calendar series, running balance, breach, lowest balance | `build_projection` v1 | T11, T12, T15, T16 pass |
| 5 Scenarios | 7–8 | Change table, apply logic, overlap trigger, compare view | Scenario module | T7–T10 pass |
| 6 Analytics | 9–10 | Explain-day, fix suggestions, variance, backtest, reserve, CSV import | Analytics views | Results match planted cases |
| 7 Quality | 11 | Concurrency test, indexes, `EXPLAIN ANALYZE`, full test run | Test report, benchmark notes | SC1 and SC2 recorded |
| 8 UI | 12 | Five screens, report export | Demo app | Demo runs end to end |
| 9 Documentation | 13 | README, schema diagram, query catalogue, limitations, 60-second pitch | Portfolio-ready repo | SC3 and SC5 pass |
| 10 Buffer | 14 | Fixes, mock interview, final review | Release tag | Definition of done met |

**Milestones**

- M1 (Day 3): schema and data ready.
- M2 (Day 6): first correct projection.
- M3 (Day 8): scenarios working.
- M4 (Day 11): analytics tested and measured.
- M5 (Day 14): release.

**Cut order if time slips:** drop F20, then F18, then F17, then F15, then F14. Never cut F6 to F11, F21, F22.

## 16. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Month-end and leap-year bugs | High | High | Compute from start date; tests T1, T2 first |
| Scope creep into a tracker | High | High | Section 6.3 cut list; review at each phase gate |
| Existing app already covers a differentiator | Medium | Medium | Phase 0 matrix; reword claims |
| Trigger race on overlap check | Medium | Medium | Parent-row lock; concurrency test |
| Performance poor at 3-year horizon | Medium | Low | Indexes; limit horizon default to 12 months |
| Time overrun | Medium | Medium | Cut order in Section 15 |
| Seed data looks unrealistic | Low | Low | State clearly that it is synthetic |
| Procedural logic becomes hard to debug | Medium | Medium | Keep logic in views where possible; small procedures |

## 17. Assumptions, Constraints, Dependencies

**Assumptions:** one developer; 10 to 14 days; local MySQL 8; the user supplies correct rules. **Constraints:** no real financial data; minimal application layer; no paid services. **Dependencies:** MySQL 8 installation, Python environment, access to free versions of comparison apps.

## 18. Integrity and Claims Policy

- Every claim in the README and resume is tagged mentally as **Implemented**, **Tested** or **Measured**. Only those go on the resume.
- Planned but unbuilt features appear only under "Future scope".
- No invented users, adoption, accuracy or speed numbers.
- Data is always described as synthetic.
- Uniqueness is stated as "differs from the tools I reviewed on \[date\]", never as "first" or "only".

## 19. Resume and Interview Plan

**Resume bullet template (fill after testing; delete anything untrue):**

> Built a MySQL 8 cash-flow forecasting engine: recurring-rule expansion with recursive CTEs, running-balance projections with window functions, stored what-if scenarios with trigger-enforced integrity, and breach explanation; validated with \[N\] tests on \[N\] synthetic rules; indexed key queries and verified plans with `EXPLAIN ANALYZE` (\[X\] ms to \[Y\] ms).

**Interview questions to prepare**

1. Rent is on the 31st. How does your engine handle February and avoid drift?
2. Why `DECIMAL` and not `FLOAT`?
3. Why a trigger for overlap, and what race condition remains?
4. Why are runs append-only?
5. Two scenario changes touch the same rule. How does the schema respond?
6. How would you make the projection faster for 10 years of data?
7. Why MySQL over MongoDB for this?
8. How do you know your forecast is right?

## 20. Future Scope (not claimed)

Multi-currency, weekend or holiday date adjustment, income prediction, multi-user access, notifications, account transfers, Account Aggregator integration.

## 21. Definition of Done

- [ ] Schema, seed, procedures, views and trigger committed
- [ ] All Must features working; Should features working or listed as cut
- [ ] Tests T1–T16 pass and the results are recorded
- [ ] Performance measured and written down, or no performance claim made
- [ ] Market matrix dated and complete
- [ ] README reproduces the demo from a fresh clone
- [ ] Limitations section written
- [ ] Resume bullet reviewed against Section 18
- [ ] Mock interview done

## Appendix A: Core DDL (starter)

```sql
CREATE TABLE recurring_rule (
  rule_id     INT AUTO_INCREMENT PRIMARY KEY,
  account_id  INT NOT NULL,
  category_id INT NOT NULL,
  label       VARCHAR(80) NOT NULL,
  amount      DECIMAL(12,2) NOT NULL,
  unit        ENUM('WEEK','MONTH') NOT NULL,
  every_n     TINYINT UNSIGNED NOT NULL DEFAULT 1,
  start_date  DATE NOT NULL,
  end_date    DATE NULL,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT ck_amount CHECK (amount <> 0),
  CONSTRAINT ck_every  CHECK (every_n >= 1),
  CONSTRAINT ck_dates  CHECK (end_date IS NULL OR end_date >= start_date),
  FOREIGN KEY (account_id)  REFERENCES account(account_id),
  FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE scenario_change (
  change_id   INT AUTO_INCREMENT PRIMARY KEY,
  scenario_id INT NOT NULL,
  rule_id     INT NULL,
  event_id    INT NULL,
  action      ENUM('SKIP','SHIFT_DAYS','SCALE') NOT NULL,
  value       DECIMAL(10,2) NULL,
  from_date   DATE NOT NULL,
  to_date     DATE NOT NULL,
  CONSTRAINT ck_target CHECK ((rule_id IS NULL) <> (event_id IS NULL)),
  CONSTRAINT ck_range  CHECK (to_date >= from_date),
  CONSTRAINT ck_value  CHECK (action = 'SKIP' OR value IS NOT NULL),
  FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id),
  FOREIGN KEY (rule_id)     REFERENCES recurring_rule(rule_id),
  FOREIGN KEY (event_id)    REFERENCES one_off_event(event_id)
);
```

**Overlap trigger sketch** (add a matching `BEFORE UPDATE`; test thoroughly):

```sql
DELIMITER //
CREATE TRIGGER trg_change_no_overlap
BEFORE INSERT ON scenario_change FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1 FROM scenario_change c
    WHERE c.scenario_id = NEW.scenario_id
      AND c.rule_id  <=> NEW.rule_id
      AND c.event_id <=> NEW.event_id
      AND c.from_date <= NEW.to_date
      AND c.to_date   >= NEW.from_date
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Overlapping scenario change for this target';
  END IF;
END//
DELIMITER ;
```

**Monthly expansion sketch** (verify edge dates on your MySQL version):

```sql
WITH RECURSIVE n AS (
  SELECT 0 AS k UNION ALL SELECT k + 1 FROM n WHERE k < 400
)
SELECT r.rule_id, r.account_id, r.amount,
       DATE_ADD(r.start_date, INTERVAL n.k * r.every_n MONTH) AS due_date
FROM recurring_rule r
JOIN n
WHERE r.is_active AND r.unit = 'MONTH'
  AND DATE_ADD(r.start_date, INTERVAL n.k * r.every_n MONTH)
      <= COALESCE(r.end_date, DATE_ADD(CURDATE(), INTERVAL 12 MONTH));
```

Note: MySQL's default `cte_max_recursion_depth` is 1000. Keep the series within that or raise the session value.

## Part II: Micro-Level Specification

Sections 1 to 21 give the macro view. Part II drills down to feature acceptance criteria, every column, every procedure, every query, every screen, and every task by phase. Hour figures are planning estimates, not measurements.

## 22. Feature Specifications and Acceptance Criteria

Each feature is done only when its acceptance criteria (AC) pass. "Reject" means the database raises an error and stores nothing.

| ID | Feature | Input | Behaviour | Output | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| F1 | Account management | name, type (SAVINGS, CURRENT, WALLET, CASH), buffer\_min | Insert, update, deactivate accounts. Name unique per user set. | Account row | AC1: negative buffer rejected. AC2: duplicate name rejected. AC3: deactivated account excluded from projection. |
| F2 | Balance checkpoints | account\_id, as\_of\_date, balance | Records a known real balance. Latest checkpoint on or before horizon start is the projection anchor. | Checkpoint row | AC1: one checkpoint per account per date. AC2: future-dated checkpoint rejected. AC3: projection with no checkpoint fails with a clear message. |
| F3 | Recurring rules | label, signed amount, unit (WEEK or MONTH), every\_n, start\_date, end\_date, category | Creates an obligation or income stream. | Rule row | AC1: amount 0 rejected. AC2: every\_n below 1 rejected. AC3: end before start rejected. AC4: is\_active false yields no occurrences. |
| F4 | One-off events | date, signed amount, label, category | Creates a single dated event. | Event row | AC1: amount 0 rejected. AC2: event outside horizon ignored by projection. |
| F5 | Categories | name, is\_essential | Tags rules and events as essential or discretionary. | Category row | AC1: name unique. AC2: category in use cannot be deleted. |
| F6 | Occurrence expansion | account\_id, horizon\_start, horizon\_end | Expands active rules and events into dated rows. | Rows (source, source\_id, due\_date, amount) | AC1: month-end clamp correct (T1, T2). AC2: no row outside rule start and end. AC3: row count equals hand count on the planted rule set. |
| F7 | Daily projected balance | account\_id, scenario\_id, horizon | Builds one balance per calendar day from the anchor plus cumulative net. | projection\_run plus projection\_day rows | AC1: one row per day, no gaps. AC2: day 1 balance equals anchor plus day 1 net. AC3: matches hand-calculated 3-month case to the paisa (T16). |
| F8 | Breach detection | run\_id, buffer\_min | Finds the first day balance is strictly below buffer and the lowest balance with its date. | first\_breach\_date, min\_balance, min\_balance\_date | AC1: planted breach date matches exactly. AC2: no breach returns NULL, not an error. AC3: balance equal to buffer is not a breach (BR10). |
| F9 | Scenarios | scenario name; changes (target, action, value, from, to) | Stores overrides without touching base rules. | scenario and scenario\_change rows | AC1: base rules unchanged after any scenario. AC2: SKIP, SHIFT\_DAYS, SCALE each change the result as defined in BR7. AC3: SHIFT or SCALE without a value rejected. |
| F10 | Overlap protection | new scenario\_change | Trigger rejects an overlapping change on the same target in the same scenario. | Error 45000 | AC1: touching ranges (same end and start day) are rejected as overlapping. AC2: same dates on a different target accepted. AC3: update path also protected. |
| F11 | Scenario comparison | two scenario ids | Runs both and returns the difference. | min balance delta, breach date delta, days below buffer delta | AC1: baseline compared with itself returns zero deltas. AC2: skipping an outflow never lowers the minimum balance. |
| F12 | Explain-day | run\_id, day | Lists events up to that day, largest outflows first, with running total. | Ordered event list | AC1: sum of listed events plus anchor equals that day's stored balance. |
| F13 | Fix suggestions | run\_id | Ranks discretionary outflows before the first breach and picks the fewest that cover the shortfall. | Suggested skip list and shortfall covered | AC1: only is\_essential = 0 items suggested. AC2: applying the suggested skips as a scenario removes the breach or reports that it cannot. |
| F14 | Plan vs actual | rule\_id, months | Compares planned and posted amounts per rule per month. | variance per month, 3-month average | AC1: a rule with no actuals shows full variance, not an error. |
| F15 | Forecast backtest | account\_id | For each past checkpoint, compares the earlier projection to the real balance. | absolute and percent error per checkpoint | AC1: needs at least two checkpoints, else a clear message. AC2: error reported as measured, never smoothed. |
| F16 | Reserve schedule | account\_id | For yearly and quarterly rules, amount spread evenly over the months of the period, cumulated by month. | Monthly reserve table | AC1: cumulative reserve reaches the full amount on the due month. |
| F17 | CSV import | CSV of date, amount, label | Loads actual transactions in one transaction. | Rows loaded and rejected counts | AC1: one bad row rolls back the whole file or is listed and skipped, chosen by a flag. AC2: re-importing the same file creates no duplicates. |
| F18 | Rule history | rule update | Trigger stores old and new values. | rule\_history row | AC1: every update to amount, dates or is\_active creates one row. |
| F19 | UI | user actions | Five screens, Section 26. | Screens | AC1: every screen runs on the seed data without error. |
| F20 | Report export | run\_id | Writes a CSV or Markdown report. | File | AC1: exported numbers equal the database numbers. |
| F21 | Synthetic data generator | seed integer | Creates repeatable data with planted cases. | Populated database | AC1: same seed gives identical data. AC2: planted cases listed in the README. |
| F22 | Automated tests | none | Runs T1 to T16 and the extended tests. | Pass or fail report | AC1: one command runs all tests. AC2: a failing test exits non-zero. |

## 23. Data Dictionary

All tables use InnoDB and `utf8mb4`. Money columns are `DECIMAL(12,2)`. Primary keys are `INT AUTO_INCREMENT` unless stated. MySQL does not allow non-deterministic functions such as `CURDATE()` inside `CHECK`, so "not in the future" rules live in procedures or triggers.

| Table | Column | Type | Null | Constraint or note |
| --- | --- | --- | --- | --- |
| account | account\_id | INT | no | PK |
| account | name | VARCHAR(60) | no | UNIQUE |
| account | account\_type | ENUM(SAVINGS, CURRENT, WALLET, CASH) | no |  |
| account | buffer\_min | DECIMAL(12,2) | no | DEFAULT 0, CHECK >= 0 |
| account | is\_active | BOOLEAN | no | DEFAULT TRUE |
| account | created\_at | TIMESTAMP | no | DEFAULT CURRENT\_TIMESTAMP |
| balance\_checkpoint | checkpoint\_id | INT | no | PK |
| balance\_checkpoint | account\_id | INT | no | FK account |
| balance\_checkpoint | as\_of\_date | DATE | no | UNIQUE with account\_id; future-date check in procedure `add_checkpoint` |
| balance\_checkpoint | balance | DECIMAL(12,2) | no | may be negative (overdrawn) |
| category | category\_id | INT | no | PK |
| category | name | VARCHAR(40) | no | UNIQUE |
| category | is\_essential | BOOLEAN | no | DEFAULT TRUE |
| recurring\_rule | rule\_id | INT | no | PK |
| recurring\_rule | account\_id | INT | no | FK account |
| recurring\_rule | category\_id | INT | no | FK category |
| recurring\_rule | label | VARCHAR(80) | no |  |
| recurring\_rule | amount | DECIMAL(12,2) | no | CHECK <> 0; negative = outflow |
| recurring\_rule | unit | ENUM(WEEK, MONTH) | no |  |
| recurring\_rule | every\_n | TINYINT UNSIGNED | no | DEFAULT 1, CHECK >= 1 |
| recurring\_rule | start\_date | DATE | no | anchor of the series |
| recurring\_rule | end\_date | DATE | yes | CHECK end >= start |
| recurring\_rule | is\_active | BOOLEAN | no | DEFAULT TRUE |
| one\_off\_event | event\_id | INT | no | PK |
| one\_off\_event | account\_id | INT | no | FK account |
| one\_off\_event | category\_id | INT | no | FK category |
| one\_off\_event | event\_date | DATE | no |  |
| one\_off\_event | amount | DECIMAL(12,2) | no | CHECK <> 0 |
| one\_off\_event | label | VARCHAR(80) | no |  |
| scenario | scenario\_id | INT | no | PK; id 1 = Baseline, seeded, undeletable |
| scenario | name | VARCHAR(60) | no | UNIQUE |
| scenario | description | VARCHAR(255) | yes |  |
| scenario | created\_at | TIMESTAMP | no | DEFAULT CURRENT\_TIMESTAMP |
| scenario\_change | change\_id | INT | no | PK |
| scenario\_change | scenario\_id | INT | no | FK scenario, not 1 (enforced in trigger) |
| scenario\_change | rule\_id | INT | yes | FK recurring\_rule; exactly one of rule\_id or event\_id |
| scenario\_change | event\_id | INT | yes | FK one\_off\_event |
| scenario\_change | action | ENUM(SKIP, SHIFT\_DAYS, SCALE) | no |  |
| scenario\_change | value | DECIMAL(10,2) | yes | required unless SKIP |
| scenario\_change | from\_date | DATE | no |  |
| scenario\_change | to\_date | DATE | no | CHECK to >= from |
| actual\_txn | txn\_id | INT | no | PK |
| actual\_txn | account\_id | INT | no | FK account |
| actual\_txn | txn\_date | DATE | no |  |
| actual\_txn | amount | DECIMAL(12,2) | no |  |
| actual\_txn | label | VARCHAR(80) | yes |  |
| actual\_txn | rule\_id | INT | yes | FK recurring\_rule (planned item it settles) |
| actual\_txn | event\_id | INT | yes | FK one\_off\_event |
| actual\_txn | source\_hash | CHAR(64) | yes | UNIQUE; SHA-256 of date, amount, label for import de-duplication |
| projection\_run | run\_id | INT | no | PK |
| projection\_run | scenario\_id | INT | no | FK scenario |
| projection\_run | account\_id | INT | no | FK account |
| projection\_run | horizon\_start, horizon\_end | DATE | no | CHECK end > start |
| projection\_run | anchor\_date, anchor\_balance | DATE, DECIMAL | no | from the checkpoint used |
| projection\_run | min\_balance, min\_balance\_date | DECIMAL, DATE | no | filled at the end of the run |
| projection\_run | first\_breach\_date | DATE | yes | NULL means no breach |
| projection\_run | days\_below\_buffer | INT | no |  |
| projection\_run | created\_at | TIMESTAMP | no | DEFAULT CURRENT\_TIMESTAMP |
| projection\_day | run\_id | INT | no | PK part 1, FK projection\_run ON DELETE CASCADE |
| projection\_day | day | DATE | no | PK part 2 |
| projection\_day | net | DECIMAL(12,2) | no | sum of that day's events |
| projection\_day | balance | DECIMAL(12,2) | no | end-of-day balance |
| rule\_history | history\_id | INT | no | PK |
| rule\_history | rule\_id | INT | no | FK recurring\_rule |
| rule\_history | changed\_at | TIMESTAMP | no | DEFAULT CURRENT\_TIMESTAMP |
| rule\_history | old\_amount, new\_amount | DECIMAL(12,2) | no |  |
| rule\_history | old\_start, new\_start, old\_end, new\_end | DATE | yes |  |
| rule\_history | old\_active, new\_active | BOOLEAN | no |  |
| calendar\_day | day | DATE | no | PK; about 1,100 rows (3 years) generated once; avoids recursion depth limits in daily series |

**Added table: `projection_event`.** Stores every occurrence used in a run, so any balance can be rebuilt from rows (differentiator U8).

| Column | Type | Null | Constraint or note |
| --- | --- | --- | --- |
| event\_id | INT | no | PK |
| run\_id | INT | no | FK projection\_run, ON DELETE CASCADE |
| due\_date | DATE | no |  |
| source\_type | ENUM(RULE, EVENT) | no |  |
| source\_id | INT | no | rule\_id or event\_id |
| label | VARCHAR(80) | no | copied at run time |
| category\_id | INT | no | FK category |
| amount | DECIMAL(12,2) | no | after scenario changes |

Index: `(run_id, due_date)`.

**Planned indexes (verify each with `EXPLAIN ANALYZE` before keeping it)**

- `recurring_rule (account_id, is_active)`
- `one_off_event (account_id, event_date)`
- `scenario_change (scenario_id, rule_id, from_date, to_date)` and `(scenario_id, event_id, from_date, to_date)`
- `actual_txn (rule_id, txn_date)` and `(account_id, txn_date)`
- `projection_run (scenario_id, account_id, run_id)`
- `balance_checkpoint (account_id, as_of_date)` is already covered by its UNIQUE key

**Relationships**

account 1-N balance\_checkpoint, recurring\_rule, one\_off\_event, actual\_txn, projection\_run. category 1-N recurring\_rule, one\_off\_event. scenario 1-N scenario\_change, projection\_run. recurring\_rule 1-N scenario\_change, actual\_txn, rule\_history. projection\_run 1-N projection\_day and projection\_event.

## 24. Views, Procedures and Triggers

### 24.1 Views

| View | Purpose | Notes |
| --- | --- | --- |
| `v_rule_occurrence` | Expands every active rule into dated occurrences | Recursive CTE with `k` up to 120 for monthly and 520 for weekly, both below the default recursion limit of 1000. Date is `DATE_ADD(start_date, INTERVAL k * every_n MONTH or WEEK)` |
| `v_latest_run` | Latest run per scenario and account | `MAX(run_id)` grouped; relies on append-only runs (BR9) |
| `v_scenario_diff` | Latest run of two scenarios side by side | Minimum balance, breach date, days below buffer |
| `v_plan_vs_actual` | Planned vs posted amount per rule per month | Left join to `actual_txn`; rules with no actuals still appear |
| `v_reserve_schedule` | Monthly set-aside for yearly and quarterly rules | Amount divided by months per period |

Views cannot take parameters, so anything that needs a horizon or scenario runs inside a procedure.

### 24.2 Procedures

| Procedure | Signature | Purpose |
| --- | --- | --- |
| `add_checkpoint` | (account\_id, as\_of\_date, balance) | Rejects future dates (error 45004); inserts a checkpoint |
| `build_projection` | (scenario\_id, account\_id, horizon\_days, OUT run\_id) | Core engine, steps below |
| `compare_scenarios` | (scenario\_a, scenario\_b, account\_id) | Returns delta in minimum balance, breach date and days below buffer |
| `explain_day` | (run\_id, day) | Returns events up to that day, largest outflows first, with running contribution |
| `suggest_fixes` | (run\_id) | Returns discretionary outflows to skip and the shortfall they cover |
| `backtest` | (account\_id) | Returns error per past checkpoint |

### 24.3 `build_projection` step by step

1. Validate: account active (else error 45002), scenario exists, horizon between 1 and 730 days (else 45003).
2. `START TRANSACTION`.
3. Find the anchor: latest checkpoint on or before today. None found raises error 45001.
4. Create `tmp_occ` as a `TEMPORARY` table: rule occurrences in the horizon plus one-off events. Creating a temporary table does not commit the transaction.
5. If the scenario is not Baseline, apply its changes to `tmp_occ`: delete skipped rows, shift dates, scale amounts. Each action is a separate statement, applied in a fixed order (SKIP, then SHIFT\_DAYS, then SCALE) so results are deterministic.
6. Aggregate `tmp_occ` to net per day. A MySQL temporary table cannot be referenced twice in one query, so copy to `tmp_net` first if a self-join is needed.
7. Insert the `projection_run` header.
8. Insert `projection_day` by joining `calendar_day` to `tmp_net` (missing days net 0; every occurrence is also saved to projection\_event) with `anchor_balance + SUM(net) OVER (ORDER BY day)`.
9. Update the header: minimum balance and date, first breach date, days below buffer.
10. `COMMIT` and return `run_id`.

An exit handler issues `ROLLBACK` and re-raises on any error, so a failed build leaves no header and no days.

Error codes (SQLSTATE 45000 with message): 45001 no checkpoint, 45002 inactive account, 45003 bad horizon, 45004 future checkpoint, 45005 overlapping scenario change, 45006 change on Baseline scenario.

### 24.4 Triggers

| Trigger | Event | Rule |
| --- | --- | --- |
| `trg_change_no_overlap` | BEFORE INSERT and BEFORE UPDATE on `scenario_change` | Reject an overlapping date range on the same scenario and target (BR6). Overlap test: `existing.from <= new.to AND existing.to >= new.from` |
| `trg_change_not_baseline` | BEFORE INSERT on `scenario_change` | Reject changes on scenario 1 |
| `trg_rule_history` | AFTER UPDATE on `recurring_rule` | Insert old and new amount, dates and active flag when any changed |

**Known limitation:** two sessions inserting overlapping changes at the same instant can both pass the trigger check. Mitigation: the procedure that inserts changes first runs `SELECT ... FOR UPDATE` on the parent `scenario` row. Test with two terminals (T14).

## 25. Query Catalogue

Every query is saved in `sql/queries/` with the question it answers. The new table `projection_event` (defined at the end of Section 23) stores each occurrence used in a run, so explain-day and fix suggestions read stored rows rather than recompute.

| ID | Question | Technique | Used by |
| --- | --- | --- | --- |
| Q1 | Which dated events fall in the horizon? | Recursive CTE, `DATE_ADD`, `UNION ALL` | F6 |
| Q2 | What is the net per calendar day, including empty days? | `LEFT JOIN` to `calendar_day`, `COALESCE` | F7 |
| Q3 | What is the balance each day? | `SUM() OVER` with an explicit `ROWS` frame | F7 |
| Q4 | First day below buffer? | `MIN(day)` with filter | F8 |
| Q5 | Lowest balance and its date? | `ORDER BY balance, day LIMIT 1` | F8 |
| Q6 | How many days below buffer? | `SUM(balance < buffer)` | F8 |
| Q7 | How do two scenarios differ? | Join of two latest runs from `v_latest_run` | F11 |
| Q8 | What made up this day's balance? | Running `SUM() OVER` over `projection_event` | F12 |
| Q9 | Which discretionary items fix the breach? | Cumulative window, ranking | F13 |
| Q10 | Planned vs actual per rule per month? | Aggregate, `AVG() OVER` with a 3-row frame | F14 |
| Q11 | How wrong were past forecasts? | Join run days to checkpoints, absolute error | F15 |
| Q12 | How much to set aside monthly for yearly bills? | Division by period months, cumulative sum | F16 |
| Q13 | Which active rules have had no posting in 3 months? | `NOT EXISTS` anti-join | Data hygiene |
| Q14 | Which categories drive the dip before the breach? | `GROUP BY` category over the breach window | F12 |

**Q3: running balance.** The explicit frame matters. The default frame with `ORDER BY` is `RANGE`, which treats rows with equal sort values as one group.

```sql
SELECT d.day, d.net,
       @anchor + SUM(d.net) OVER (
         ORDER BY d.day
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS balance
FROM (
  SELECT cd.day, COALESCE(SUM(n.amount), 0) AS net
  FROM calendar_day cd
  LEFT JOIN tmp_occ n ON n.due_date = cd.day
  WHERE cd.day BETWEEN @start AND @end
  GROUP BY cd.day
) d;
```

**Q4 to Q6: breach summary from stored days.**

```sql
SELECT MIN(CASE WHEN balance < @buffer THEN day END) AS first_breach_date,
       SUM(balance < @buffer)                         AS days_below_buffer,
       MIN(balance)                                   AS min_balance
FROM projection_day
WHERE run_id = @run;
```

**Q9: fix suggestions.** Shortfall is `buffer_min - min_balance`. This addresses the first breach only, and the result states that.

```sql
WITH cand AS (
  SELECT pe.event_id, pe.due_date, pe.label, -pe.amount AS saving
  FROM projection_event pe
  JOIN category c ON c.category_id = pe.category_id
  WHERE pe.run_id = @run AND c.is_essential = 0
    AND pe.amount < 0 AND pe.due_date <= @first_breach
), ranked AS (
  SELECT cand.*,
         SUM(saving) OVER (
           ORDER BY saving DESC, due_date, event_id
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_saving
  FROM cand
)
SELECT * FROM ranked
WHERE cum_saving - saving < @shortfall;
```

**Q10: planned vs actual with a 3-month average.**

```sql
SELECT m.rule_id, m.ym, m.planned, m.actual,
       AVG(m.actual) OVER (
         PARTITION BY m.rule_id ORDER BY m.ym
         ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS avg_3m
FROM (
  SELECT r.rule_id, DATE_FORMAT(a.txn_date, '%Y-%m') AS ym,
         r.amount AS planned, SUM(a.amount) AS actual
  FROM recurring_rule r
  JOIN actual_txn a ON a.rule_id = r.rule_id
  GROUP BY r.rule_id, ym, r.amount
) m;
```

**Q13: stale rules.**

```sql
SELECT r.rule_id, r.label
FROM recurring_rule r
WHERE r.is_active
  AND NOT EXISTS (
    SELECT 1 FROM actual_txn a
    WHERE a.rule_id = r.rule_id
      AND a.txn_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH));
```

These snippets are untested drafts. Run each against the planted cases before relying on it.

## 26. Application Layer Specification

**Rule:** the UI and CLI contain no business logic. They call procedures and views and display results. Errors from SQLSTATE 45000 are shown as the stored message.

### 26.1 Screens (Streamlit or equivalent)

| # | Screen | Inputs | Shows | Backed by |
| --- | --- | --- | --- | --- |
| 1 | Rules and events | Add or edit rule, add event, import CSV | Table of rules with category, amount, frequency, dates, active flag | F1 to F5, F17 |
| 2 | Projection | Account, scenario, horizon (30 to 730 days) | Balance line chart with buffer line and breach marker. Cards: anchor balance, lowest balance and date, first breach date, days below buffer | F6 to F8 |
| 3 | Scenario compare | Two scenarios | Delta table, overlaid balance lines | F9 to F11 |
| 4 | Explain and fix | Day (defaults to first breach) | Events behind that day, category contribution before the breach, suggested skips, button "Save as scenario" that creates SKIP changes | F12, F13 |
| 5 | Reserve and accuracy | Account | Reserve schedule, plan vs actual table, backtest error table | F14 to F16 |

### 26.2 CLI commands

| Command | Action |
| --- | --- |
| `python cli.py init-db` | Runs all SQL files in order |
| `python cli.py seed --seed 42` | Loads synthetic data |
| `python cli.py project --account 1 --scenario 1 --days 365` | Calls `build_projection`, prints summary |
| `python cli.py compare 1 2 --account 1` | Calls `compare_scenarios` |
| `python cli.py explain --run 7 --day 2027-03-05` | Calls `explain_day` |
| `python cli.py fix --run 7` | Calls `suggest_fixes` |
| `python cli.py import actuals.csv` | Loads actual transactions |
| `python cli.py test` | Runs the test suite |

### 26.3 Out of scope for the interface

Login, multi-user data separation, mobile layout, notifications, theming.

## 27. Repository, Environment and Workflow

```text
ebbline/
  README.md
  .env.example          (placeholders only; real .env is git-ignored)
  docker-compose.yml    (optional: mysql:8.0)
  sql/
    00_schema.sql
    01_views.sql
    02_procedures.sql
    03_triggers.sql
    04_indexes.sql
    queries/            (Q1 to Q14, one file each)
    tests/              (T1 to T16 and extended tests)
  app/
    db.py               (connection, parameterised calls)
    seed.py             (fixed-seed generator, planted cases)
    cli.py
    ui.py
  tests/run_tests.py
  docs/
    pid.md              (this document, exported)
    er-diagram.png
    market-matrix.md
    benchmarks.md       (measured results only)
```

**Environment:** MySQL 8.0 or later, Python 3.11 or later, packages `mysql-connector-python` and `streamlit`. Create database `ebbline` and an app user with `SELECT, INSERT, UPDATE, DELETE, EXECUTE` on it only.

**Git workflow**

- One branch per phase, named `phase-N-topic`; merge to `main` only when the phase exit check passes.
- Commit messages: `feat:`, `fix:`, `test:`, `docs:`, `perf:` prefixes, one logical change each.
- Tags at milestones: `v0.1` (M1), `v0.2` (M2), `v0.3` (M3), `v0.4` (M4), `v1.0` (M5).
- Never commit `.env`, real data or credentials. Seed data is synthetic and says so in the README.

## 28. Task-Level Phase Plan

Budget: about 69 planning hours over 14 days (roughly 5 hours a day). These are estimates, not measurements. Update them at each phase gate with the actual hours.

**Critical path:** schema, expansion, projection, scenarios, analytics. Nothing in Phases 6 to 8 starts before Phase 4 passes its exit check.

### 28.1 Tasks and hours

| Phase | Day | Task | Hours |
| --- | --- | --- | --- |
| 0 Setup and validation | 1 | Install MySQL 8, confirm `SELECT VERSION()`, check `cte_max_recursion_depth` | 1.0 |
| 0 | 1 | Create repo, folders, `.gitignore`, `.env.example`, README skeleton | 0.5 |
| 0 | 1 | Draft ER sketch on paper | 0.5 |
| 0 | 1 | Pick 5 apps (include 2 global ones with forecasting), trial or read official docs, fill dated matrix | 2.5 |
| 0 | 1 | Search the name "Ebbline" on Google, GitHub and both app stores; record the result | 0.5 |
| 1 Schema | 2 | Final ER diagram in Workbench, export image | 1.0 |
| 1 | 2 | Write `00_schema.sql` in dependency order with all constraints | 2.0 |
| 1 | 2 | Seed categories and the Baseline scenario; write `add_checkpoint` | 0.5 |
| 1 | 2 | Write one rejecting test per constraint (bad amount, bad dates, duplicates, FK) | 1.5 |
| 2 Seed data | 3 | List planted cases (see 28.2) | 1.0 |
| 2 | 3 | Write `seed.py` with fixed seed | 2.5 |
| 2 | 3 | Fill `calendar_day`; verify row counts and planted cases | 1.0 |
| 2 | 3 | README data note: synthetic, how to regenerate | 0.5 |
| 3 Expansion | 4 | Monthly expansion from start date with `every_n` | 2.0 |
| 3 | 4 | Weekly expansion | 1.0 |
| 3 | 4 | Tests T1 to T6 as SQL files | 2.0 |
| 3 | 5 | One-off events union, inactive and date filters, view `v_rule_occurrence` | 2.0 |
| 3 | 5 | Horizon bounds, review, commit, buffer time | 3.0 |
| 4 Projection | 6 | Hand-calculate a 3-month case in a spreadsheet outside the database (for T16) | 1.0 |
| 4 | 6 | Temporary tables and daily net via `calendar_day` | 1.0 |
| 4 | 6 | Running balance, run header, `projection_event` rows | 1.5 |
| 4 | 6 | Breach, lowest balance, days below buffer | 0.5 |
| 4 | 6 | Exit handler, error codes 45001 to 45003, tests T11, T12, T15, T16 | 1.0 |
| 5 Scenarios | 7 | Scenario tables, `trg_change_no_overlap` (insert and update), baseline guard | 2.5 |
| 5 | 7 | Apply SKIP, SHIFT\_DAYS, SCALE in `build_projection` | 3.0 |
| 5 | 8 | `compare_scenarios` and `v_scenario_diff` | 1.5 |
| 5 | 8 | Tests T7 to T10; draft the two-terminal concurrency test | 2.0 |
| 5 | 8 | Buffer | 1.0 |
| 6 Analytics | 9 | `explain_day`, Q14 contribution query | 1.5 |
| 6 | 9 | `suggest_fixes` | 2.0 |
| 6 | 9 | `v_plan_vs_actual` | 1.5 |
| 6 | 10 | `backtest` | 2.0 |
| 6 | 10 | `v_reserve_schedule` | 1.0 |
| 6 | 10 | CSV import with SHA-256 de-duplication | 1.5 |
| 6 | 10 | `trg_rule_history` (Could) | 0.5 |
| 7 Quality | 11 | `run_tests.py` running all SQL tests, non-zero exit on failure | 1.5 |
| 7 | 11 | Two-terminal concurrency test (T14) | 1.0 |
| 7 | 11 | `EXPLAIN ANALYZE` on build, compare, explain, backtest before indexes | 1.0 |
| 7 | 11 | Add indexes, re-measure, record in `benchmarks.md` | 1.0 |
| 7 | 11 | Tag `v0.4` | 0.5 |
| 8 UI | 12 | Five screens | 4.0 |
| 8 | 12 | Report export and error display | 1.0 |
| 9 Documentation | 13 | README: quickstart, ER image, query catalogue, limitations, matrix link | 3.0 |
| 9 | 13 | Screenshots, 60-second pitch notes, export this document | 1.0 |
| 9 | 13 | Resume bullet using measured values only | 0.5 |
| 9 | 13 | Name and claim review (Section 18) | 0.5 |
| 10 Buffer and release | 14 | Fix defects, mock interview with a peer (Section 19), Definition of Done check, tag `v1.0` | 4.0 |

### 28.2 Planted cases for seed data

| ID | Case | Used by |
| --- | --- | --- |
| P1 | Monthly rule starting on the 31st | T1 |
| P2 | Monthly rule starting 29 Feb of a leap year | T2 |
| P3 | Rule every 2 weeks | T3 |
| P4 | Yearly insurance premium (`MONTH`, `every_n` 12) | T4, F16 |
| P5 | Account A engineered to breach on a known date | T15, F8 |
| P6 | Account B engineered never to breach | T11 |
| P7 | Active rule with no postings in 3 months | Q13 |
| P8 | Rules whose actuals deviate 5 to 15 percent from plan | F14 |
| P9 | Three checkpoints for one account | F15 |
| P10 | A discretionary outflow before the planted breach | F13 |

### 28.3 Phase exit checks

| Phase | Exit check |
| --- | --- |
| 0 | Matrix dated with at least 5 apps; name search recorded |
| 1 | Every negative constraint test rejects; ER diagram committed |
| 2 | Same seed gives identical data twice; planted cases verified by count |
| 3 | T1 to T6 pass |
| 4 | T11, T12, T15, T16 pass; failed build leaves no rows |
| 5 | T7 to T10 pass; baseline untouched by any scenario |
| 6 | Analytics match planted cases; F12 to F16 acceptance criteria pass |
| 7 | Full suite passes; benchmarks recorded with version and hardware |
| 8 | Demo runs end to end on seed data |
| 9 | Fresh clone reproduces demo (SC3) |
| 10 | Definition of Done complete; tag `v1.0` |

### 28.4 Slip rules

- Falling more than half a day behind at a gate triggers the cut order in Section 15.
- A phase is never started on a red test from an earlier phase.
- At each gate: run all tests, commit, write actual hours and one lesson in the decision log.

## 29. Extended Test and Measurement Plan

These add to T1 to T16 in Section 14.

| ID | Case | Expected |
| --- | --- | --- |
| T17 | Weekly rule with SHIFT\_DAYS crossing 31 Dec | Dates move into the next year correctly |
| T18 | SKIP range covering exactly one occurrence | Only that occurrence removed |
| T19 | SCALE 1.5 on an outflow | Amount becomes 1.5 times, rounded to 2 decimals (decision D9) |
| T20 | Insert a change on Baseline | Error 45006 |
| T21 | Checkpoint 10 days old | Projection starts the day after the checkpoint, so events in the gap are included (decision D8) |
| T22 | Import the same CSV twice | Second load adds zero rows |
| T23 | CSV with one invalid row | Behaviour matches the chosen flag: whole file rolls back, or row is listed and skipped |
| T24 | Horizon 0 and 731 days | Error 45003 |
| T25 | Inactive account | Error 45002 |
| T26 | Delete a category that is in use | Rejected by FK |
| T27 | Invariant: for every run, sum of `projection_event.amount` equals sum of `projection_day.net` | Equal for all runs |
| T28 | Invariant: each day's balance equals the previous day's balance plus its net | True for all rows in all runs |
| T29 | Force an error mid-build | No `projection_run` row and no day or event rows remain |
| T30 | Update a rule's amount | One `rule_history` row with old and new values |
| T31 | Compare baseline with itself | All deltas zero |
| T32 | Same seed generated twice | Identical data (hash of all tables matches) |

**Invariant tests (T27, T28)** run over every stored run, not one sample. They catch whole classes of bugs cheaply.

### 29.1 Performance measurement protocol

1. Record MySQL version, OS, CPU, RAM and whether MySQL runs in Docker.
2. Define three data sizes and label them honestly: seed size (about 3 accounts and 60 rules), and a larger synthetic stress set you generate yourself (for example 20 accounts and 1,000 rules). Do not call the stress set real-world.
3. For each query in the benchmark list (`build_projection` for 365 and 730 days, `compare_scenarios`, `explain_day`, `backtest`), run 5 times after a warm-up run and record the median.
4. Capture `EXPLAIN ANALYZE` output before and after each index.
5. Keep an index only if it improves a measured query. Remove it if not.
6. Store results in `docs/benchmarks.md` as a table: query, data size, indexes, median ms, plan note.

SC2 target (2 seconds for a 3-year build on seed data) is checked here. A miss is reported, then fixed or the target is restated with the reason.

### 29.2 Forecast accuracy note

Backtest error on synthetic data reflects how the generator was written, not real-life accuracy. The README says so. Any accuracy number on a resume would need real personal data used with consent and described as a single-person trial.

### 29.3 Data quality checks on the seed

No rule with `end_date` before `start_date`; no orphan foreign keys; checkpoints in date order; at least one account with a breach and one without; row counts match the README.

## 30. Decision Log, Extended Risks, Open Questions and Glossary

### 30.1 Decision log

| ID | Decision | Reason |
| --- | --- | --- |
| D1 | Money as `DECIMAL(12,2)`, never `FLOAT` | Exact arithmetic; binary floats cannot represent most decimal fractions |
| D2 | Recurrence is `unit` (WEEK or MONTH) plus `every_n` | Quarterly and yearly are `MONTH` with 3 and 12; one mechanism |
| D3 | Occurrence dates computed from `start_date`, not the previous date | Avoids drift after month-end clamping |
| D4 | Projection runs are append-only | No overwrite races; history of past forecasts powers the backtest |
| D5 | `calendar_day` table instead of a recursive date series | Avoids the default recursion limit of 1000 |
| D6 | Explicit `ROWS` frame on running sums | Default `RANGE` frame treats ties as one group |
| D7 | Overlap protection by trigger plus parent-row lock | MySQL has no exclusion constraint |
| D8 | Projection starts the day after the anchor checkpoint | Events between the checkpoint and today must not be lost |
| D9 | `SCALE` results rounded to 2 decimals after multiplying | One rounding point, documented; MySQL rounds exact decimals half away from zero |
| D10 | Scenario actions applied in fixed order: SKIP, SHIFT\_DAYS, SCALE | Deterministic results |
| D11 | `projection_event` stored per run | Traceability and cheap explain-day |
| D12 | No logic in the UI layer | SQL is the product; keeps the project database-first |

### 30.2 Additional risks

| Risk | Mitigation |
| --- | --- |
| Hand calculation and SQL differ by a few paise | Fix rounding rule first (D9); compare at 2 decimals |
| MySQL version differences (`CHECK` enforced from 8.0.16, `EXPLAIN ANALYZE` from 8.0.18) | Pin and record the version; test on it |
| Temporary table limits (cannot reference twice in one query) | Copy to a second temporary table when needed |
| Name collision | Search recorded in Phase 0; use "personal project" wording |
| Synthetic data looks too tidy | Add noisy actuals and irregular events on purpose |
| Burnout or lost days | Cut order, buffer day, no work on a red test |
| Interview questions go beyond what was built | Section 18: claim only what was implemented, tested or measured |

### 30.3 Open questions (decide during build, record in 30.1)

- Should rules landing on weekends shift to the next business day? Default no (future scope).
- How old can a checkpoint be before the projection warns? Proposed: 90 days.
- Should transfers between accounts exist? Default no (future scope).
- Should CSV import default to whole-file rollback or skip-and-report? Decide at Phase 6.

### 30.4 Glossary

| Term | Meaning |
| --- | --- |
| Anchor | The known balance a projection starts from |
| Buffer | The minimum balance the user wants to keep |
| Breach | A day whose balance is strictly below the buffer |
| Checkpoint | A recorded real balance on a date |
| Horizon | The number of future days projected |
| Occurrence | One dated instance of a rule or event |
| Scenario | A named set of what-if changes layered on the baseline |
| Planted case | Synthetic data built to produce a known result for testing |
| Append-only | Rows are added, never overwritten |
| Frame | The set of rows a window function sums or averages over |
| Ebb | The falling of the balance toward the buffer line |
