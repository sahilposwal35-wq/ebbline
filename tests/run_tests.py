import sys
import os
import mysql.connector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_connection

def run_constraint_tests():
    print("Running Phase 1 negative constraint tests...")
    conn = get_connection()
    cursor = conn.cursor()

    tests = [
        ("C1: Negative account buffer rejected",
         "INSERT INTO account (name, account_type, buffer_min) VALUES ('Neg Buffer Test', 'SAVINGS', -50.00)",
         True),
        ("C2: Duplicate account name rejected",
         "INSERT INTO account (name, account_type, buffer_min) VALUES ('Salary Acc', 'SAVINGS', 1000.00); "
         "INSERT INTO account (name, account_type, buffer_min) VALUES ('Salary Acc', 'CURRENT', 500.00)",
         True),
        ("C3: Rule zero amount rejected",
         "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date) "
         "VALUES (1, 1, 'Zero Amount', 0.00, 'MONTH', 1, '2026-01-01')",
         True),
        ("C4: Rule every_n below 1 rejected",
         "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date) "
         "VALUES (1, 1, 'Bad Every', 500.00, 'MONTH', 0, '2026-01-01')",
         True),
        ("C5: Rule end date before start date rejected",
         "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date, end_date) "
         "VALUES (1, 1, 'End Before Start', 500.00, 'MONTH', 1, '2026-06-01', '2026-05-01')",
         True),
        ("C6: Event zero amount rejected",
         "INSERT INTO one_off_event (account_id, category_id, event_date, amount, label) "
         "VALUES (1, 1, '2026-05-01', 0.00, 'Zero Event')",
         True),
        ("C7: Change with both targets null rejected",
         "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
         "VALUES (1, NULL, NULL, 'SKIP', NULL, '2026-01-01', '2026-01-31')",
         True),
        ("C8: Change with both targets set rejected",
         "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
         "VALUES (1, 1, 1, 'SKIP', NULL, '2026-01-01', '2026-01-31')",
         True),
        ("C9: Change to_date before from_date rejected",
         "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
         "VALUES (1, 1, NULL, 'SKIP', NULL, '2026-05-01', '2026-04-01')",
         True),
        ("C10: Change SCALE with null value rejected",
         "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
         "VALUES (1, 1, NULL, 'SCALE', NULL, '2026-05-01', '2026-05-31')",
         True),
        ("C11: Future checkpoint rejected by add_checkpoint",
         "CALL add_checkpoint(1, '2099-01-01', 10000.00)",
         True),
        ("C12: Delete category in use rejected by FK",
         "DELETE FROM category WHERE category_id = 1",
         True)
    ]

    passed = 0
    failed = 0

    # Ensure baseline account exists for FK tests
    try:
        cursor.execute("INSERT IGNORE INTO account (account_id, name, account_type, buffer_min) VALUES (1, 'Primary Account', 'SAVINGS', 1000.00)")
        cursor.execute("INSERT IGNORE INTO recurring_rule (rule_id, account_id, category_id, label, amount, unit, every_n, start_date) VALUES (1, 1, 1, 'Salary', 50000.00, 'MONTH', 1, '2026-01-01')")
        cursor.execute("INSERT IGNORE INTO one_off_event (event_id, account_id, category_id, event_date, amount, label) VALUES (1, 1, 1, '2026-01-15', 5000.00, 'Bonus')")
        conn.commit()
    except Exception as e:
        pass

    for name, sql, expect_error in tests:
        conn.rollback()
        try:
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                cursor.execute(stmt)
            conn.commit()
            if expect_error:
                print(f"FAIL: {name} (expected error but statement succeeded)")
                failed += 1
            else:
                print(f"PASS: {name}")
                passed += 1
        except Exception as ex:
            conn.rollback()
            if expect_error:
                print(f"PASS: {name} (correctly rejected with: {ex})")
                passed += 1
            else:
                print(f"FAIL: {name} (unexpected error: {ex})")
                failed += 1

    cursor.close()
    conn.close()
    return passed, failed

def run_expansion_tests():
    print("\nRunning Phase 3 expansion tests (T1 to T6)...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    passed = 0
    failed = 0

    # T1: Monthly rule starting 31 Jan (Rule 9)
    cursor.execute("""
        SELECT due_date FROM v_rule_occurrence 
        WHERE source_id = 9 AND due_date BETWEEN '2026-01-01' AND '2026-04-01' 
        ORDER BY due_date
    """)
    rows = cursor.fetchall()
    dates = [r['due_date'].strftime('%Y-%m-%d') for r in rows]
    if dates == ['2026-01-31', '2026-02-28', '2026-03-31']:
        print("PASS: T1 Monthly rule starting 31 Jan (Feb 28 clamp, Mar 31 no drift)")
        passed += 1
    else:
        print(f"FAIL: T1 Expected ['2026-01-31', '2026-02-28', '2026-03-31'] but got {dates}")
        failed += 1

    # T2: Leap-year 29 Feb start (Rule 10)
    cursor.execute("""
        SELECT due_date FROM v_rule_occurrence 
        WHERE source_id = 10 AND due_date BETWEEN '2024-01-01' AND '2028-12-31' 
        ORDER BY due_date
    """)
    rows = cursor.fetchall()
    dates = [r['due_date'].strftime('%Y-%m-%d') for r in rows]
    if dates == ['2024-02-29', '2025-02-28', '2026-02-28', '2027-02-28', '2028-02-29']:
        print("PASS: T2 Leap-year 29 Feb start (clamps to 28 Feb in non-leap, 29 Feb in leap year)")
        passed += 1
    else:
        print(f"FAIL: T2 Expected 2024/2028 leap clamp but got {dates}")
        failed += 1

    # T3: Weekly rule, every 2 weeks (Rule 6)
    cursor.execute("""
        SELECT due_date, DATEDIFF(due_date, LAG(due_date) OVER (ORDER BY due_date)) AS diff_days
        FROM v_rule_occurrence 
        WHERE source_id = 6 AND due_date BETWEEN '2026-10-01' AND '2026-12-31' 
        ORDER BY due_date
    """)
    rows = cursor.fetchall()
    diffs = [r['diff_days'] for r in rows[1:]]
    if len(diffs) > 0 and all(d == 14 for d in diffs):
        print(f"PASS: T3 Weekly rule every 2 weeks (14-day spacing across {len(diffs)} periods)")
        passed += 1
    else:
        print(f"FAIL: T3 Expected all diffs to be 14 days, got {diffs}")
        failed += 1

    # T4: Yearly rule via every_n = 12 (Rule 11)
    cursor.execute("""
        SELECT COUNT(*) AS occ_count FROM v_rule_occurrence 
        WHERE source_id = 11 AND due_date BETWEEN '2026-10-01' AND '2027-10-01'
    """)
    cnt = cursor.fetchone()['occ_count']
    if cnt == 1:
        print("PASS: T4 Yearly rule via every_n = 12 (exactly 1 occurrence per year)")
        passed += 1
    else:
        print(f"FAIL: T4 Expected 1 occurrence per year, got {cnt}")
        failed += 1

    # T5: Rule ends before horizon (Rule 15)
    cursor.execute("""
        SELECT COUNT(*) AS occ_after_end FROM v_rule_occurrence 
        WHERE source_id = 15 AND due_date > '2026-05-01'
    """)
    cnt = cursor.fetchone()['occ_after_end']
    if cnt == 0:
        print("PASS: T5 Rule ends before horizon (0 occurrences after end date)")
        passed += 1
    else:
        print(f"FAIL: T5 Expected 0 occurrences after end date, got {cnt}")
        failed += 1

    # T6: Rule starts after horizon
    cursor.execute("""
        SELECT COUNT(*) AS occ_future_start FROM v_rule_occurrence 
        WHERE start_date > '2028-12-31' AND due_date <= '2027-12-31'
    """)
    cnt = cursor.fetchone()['occ_future_start']
    if cnt == 0:
        print("PASS: T6 Rule starts after horizon (0 occurrences)")
        passed += 1
    else:
        print(f"FAIL: T6 Expected 0 occurrences, got {cnt}")
        failed += 1

    cursor.close()
    conn.close()
    return passed, failed

def run_projection_tests():
    print("\nRunning Phase 4 projection and breach tests (T11, T12, T15, T16, T24, T25, T29)...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    passed = 0
    failed = 0

    # T11: No breach account (Account 2)
    try:
        cursor.callproc('build_projection', [1, 2, 365, 0])
        cursor.execute("SELECT MAX(run_id) AS rid FROM projection_run WHERE account_id = 2 AND scenario_id = 1")
        rid = cursor.fetchone()['rid']
        cursor.execute("SELECT first_breach_date, days_below_buffer, min_balance FROM projection_run WHERE run_id = %s", [rid])
        row = cursor.fetchone()
        if row['first_breach_date'] is None and row['days_below_buffer'] == 0 and row['min_balance'] >= 20000:
            print("PASS: T11 No rules/never breach account (first_breach_date is NULL, 0 days below buffer)")
            passed += 1
        else:
            print(f"FAIL: T11 Unexpected values: {row}")
            failed += 1
    except Exception as ex:
        print(f"FAIL: T11 Exception: {ex}")
        failed += 1

    # T12: Breach on Day 1
    try:
        cursor.execute("INSERT INTO account (account_id, name, account_type, buffer_min) VALUES (990, 'Day 1 Breach Acc', 'SAVINGS', 50000.00)")
        cursor.execute("INSERT INTO balance_checkpoint (account_id, as_of_date, balance) VALUES (990, '2026-10-01', 30000.00)")
        cursor.callproc('build_projection', [1, 990, 30, 0])
        cursor.execute("SELECT MAX(run_id) AS rid FROM projection_run WHERE account_id = 990")
        rid = cursor.fetchone()['rid']
        cursor.execute("SELECT horizon_start, first_breach_date FROM projection_run WHERE run_id = %s", [rid])
        row = cursor.fetchone()
        cursor.execute("DELETE FROM projection_run WHERE account_id = 990")
        cursor.execute("DELETE FROM account WHERE account_id = 990")
        if row['first_breach_date'] == row['horizon_start']:
            print(f"PASS: T12 Day 1 breach (first breach {row['first_breach_date']} equals horizon start)")
            passed += 1
        else:
            print(f"FAIL: T12 Expected breach on {row['horizon_start']}, got {row['first_breach_date']}")
            failed += 1
    except Exception as ex:
        print(f"FAIL: T12 Exception: {ex}")
        failed += 1

    # T15: Planted breach matches exact date (2026-10-18)
    try:
        cursor.callproc('build_projection', [1, 1, 365, 0])
        cursor.execute("SELECT MAX(run_id) AS rid FROM projection_run WHERE account_id = 1 AND scenario_id = 1")
        rid = cursor.fetchone()['rid']
        cursor.execute("SELECT first_breach_date FROM projection_run WHERE run_id = %s", [rid])
        row = cursor.fetchone()
        if str(row['first_breach_date']) == '2026-10-18':
            print("PASS: T15 Planted breach date matches exactly 2026-10-18")
            passed += 1
        else:
            print(f"FAIL: T15 Expected 2026-10-18, got {row['first_breach_date']}")
            failed += 1
    except Exception as ex:
        print(f"FAIL: T15 Exception: {ex}")
        failed += 1

    # T16: Hand-calculated 3-month case matches to the paisa
    try:
        from scripts.compute_t16_case import compute
        expected = compute()
        cursor.callproc('build_projection', [1, 1, 90, 0])
        cursor.execute("SELECT MAX(run_id) AS rid FROM projection_run WHERE account_id = 1 AND scenario_id = 1")
        rid = cursor.fetchone()['rid']
        cursor.execute("SELECT day, net, balance FROM projection_day WHERE run_id = %s ORDER BY day", [rid])
        db_rows = cursor.fetchall()
        mismatches = 0
        for (exp_date, exp_net, exp_bal), db_row in zip(expected, db_rows):
            if exp_date != db_row['day'] or exp_net != db_row['net'] or exp_bal != db_row['balance']:
                mismatches += 1
        if mismatches == 0 and len(db_rows) == 90:
            print(f"PASS: T16 Hand-calculated 3-month case matches all {len(db_rows)} days to the exact paisa")
            passed += 1
        else:
            print(f"FAIL: T16 Mismatches found: {mismatches}")
            failed += 1
    except Exception as ex:
        print(f"FAIL: T16 Exception: {ex}")
        failed += 1

    # T24: Horizon 0 and 731 rejected with 45003
    try:
        cursor.callproc('build_projection', [1, 1, 0, 0])
        print("FAIL: T24 Horizon 0 accepted unexpectedly")
        failed += 1
    except Exception as ex:
        if '45003' in str(ex):
            print("PASS: T24 Horizon 0 rejected with error 45003")
            passed += 1
        else:
            print(f"FAIL: T24 Unexpected error for horizon 0: {ex}")
            failed += 1

    try:
        cursor.callproc('build_projection', [1, 1, 731, 0])
        print("FAIL: T24 Horizon 731 accepted unexpectedly")
        failed += 1
    except Exception as ex:
        if '45003' in str(ex):
            print("PASS: T24 Horizon 731 rejected with error 45003")
            passed += 1
        else:
            print(f"FAIL: T24 Unexpected error for horizon 731: {ex}")
            failed += 1

    # T25: Inactive account rejected with 45002
    try:
        cursor.execute("INSERT INTO account (account_id, name, account_type, buffer_min, is_active) VALUES (991, 'Inactive Acc', 'SAVINGS', 1000.00, FALSE)")
        cursor.callproc('build_projection', [1, 991, 30, 0])
        print("FAIL: T25 Inactive account accepted unexpectedly")
        failed += 1
    except Exception as ex:
        if '45002' in str(ex):
            print("PASS: T25 Inactive account rejected with error 45002")
            passed += 1
        else:
            print(f"FAIL: T25 Unexpected error for inactive account: {ex}")
            failed += 1
    finally:
        cursor.execute("DELETE FROM account WHERE account_id = 991")

    # T29: Atomic rollback on failure leaves no rows
    cursor.execute("SELECT COUNT(*) AS c FROM projection_run")
    runs_before = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM projection_day")
    days_before = cursor.fetchone()['c']
    try:
        cursor.callproc('build_projection', [1, 1, 800, 0])
    except Exception:
        pass
    cursor.execute("SELECT COUNT(*) AS c FROM projection_run")
    runs_after = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM projection_day")
    days_after = cursor.fetchone()['c']
    if runs_before == runs_after and days_before == days_after:
        print("PASS: T29 Failed build rolls back cleanly leaving no orphaned header or day rows")
        passed += 1
    else:
        print(f"FAIL: T29 Orphaned rows created on failed build (runs {runs_before}->{runs_after}, days {days_before}->{days_after})")
        failed += 1

    cursor.close()
    conn.close()
    return passed, failed

def main():
    total_passed = 0
    total_failed = 0

    p, f = run_constraint_tests()
    total_passed += p
    total_failed += f

    p_exp, f_exp = run_expansion_tests()
    total_passed += p_exp
    total_failed += f_exp

    p_proj, f_proj = run_projection_tests()
    total_passed += p_proj
    total_failed += f_proj

    print(f"\nTest Summary: {total_passed} passed, {total_failed} failed.")
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
