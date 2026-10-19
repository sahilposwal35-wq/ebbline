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

def main():
    total_passed = 0
    total_failed = 0

    p, f = run_constraint_tests()
    total_passed += p
    total_failed += f

    print(f"\nTest Summary: {total_passed} passed, {total_failed} failed.")
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
