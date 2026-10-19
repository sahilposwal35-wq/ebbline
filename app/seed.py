import sys
import os
import random
import hashlib
import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_connection

def compute_source_hash(txn_date, amount, label):
    raw = f"{txn_date}|{Decimal(str(amount)):.2f}|{label.strip()}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def seed_database(seed_val=42):
    random.seed(seed_val)
    conn = get_connection()
    cursor = conn.cursor()

    print(f"Seeding database with fixed seed {seed_val}...")

    # Disable foreign keys for clean reset
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = [
        "projection_event", "projection_day", "projection_run",
        "actual_txn", "scenario_change", "rule_history",
        "recurring_rule", "one_off_event", "balance_checkpoint",
        "account", "scenario", "category", "calendar_day"
    ]
    for tbl in tables:
        cursor.execute(f"DELETE FROM {tbl};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 1. Populate calendar_day (2025-01-01 to 2028-12-31, 4 full years = 1461 days)
    start_cal = datetime.date(2025, 1, 1)
    end_cal = datetime.date(2028, 12, 31)
    curr_cal = start_cal
    cal_days = []
    while curr_cal <= end_cal:
        cal_days.append((curr_cal,))
        curr_cal += datetime.timedelta(days=1)
    cursor.executemany("INSERT INTO calendar_day (day) VALUES (%s)", cal_days)
    print(f"Inserted {len(cal_days)} calendar days.")

    # 2. Populate Categories
    categories = [
        (1, 'Salary and Income', True),
        (2, 'Housing and Rent', True),
        (3, 'Utilities and Bills', True),
        (4, 'Groceries', True),
        (5, 'Loan EMIs', True),
        (6, 'Insurance', True),
        (7, 'Investments and SIPs', True),
        (8, 'Subscriptions', False),
        (9, 'Dining and Leisure', False),
        (10, 'Shopping', False)
    ]
    cursor.executemany("INSERT INTO category (category_id, name, is_essential) VALUES (%s, %s, %s)", categories)

    # 3. Populate Scenarios
    scenarios = [
        (1, 'Baseline', 'Default baseline plan without what-if overrides'),
        (2, 'Skip Subscriptions & Dining', 'What-if test skipping discretionary outflows during breach window'),
        (3, 'Shift Annual Insurance', 'Shift insurance payment by 15 days to bridge salary credit'),
        (4, 'Scale Salary 10% Hike', 'Test impact of 10% salary increase across the entire year')
    ]
    cursor.executemany("INSERT INTO scenario (scenario_id, name, description) VALUES (%s, %s, %s)", scenarios)

    # 4. Populate Accounts
    # Account 1: Planted breach account
    # Account 2: Never breaches account
    # Account 3: Freelance / irregular account
    accounts = [
        (1, 'Salaried Primary (Engineered Breach)', 'SAVINGS', Decimal('15000.00'), True),
        (2, 'Emergency Reserve (Never Breaches)', 'SAVINGS', Decimal('20000.00'), True),
        (3, 'Freelance & Daily Expenses', 'CURRENT', Decimal('5000.00'), True)
    ]
    cursor.executemany("INSERT INTO account (account_id, name, account_type, buffer_min, is_active) VALUES (%s, %s, %s, %s, %s)", accounts)

    # 5. Populate Checkpoints (P9: Three checkpoints for Account 1)
    checkpoints = [
        (1, 1, datetime.date(2026, 8, 1), Decimal('90000.00')),
        (2, 1, datetime.date(2026, 9, 1), Decimal('92000.00')),
        (3, 1, datetime.date(2026, 10, 1), Decimal('95000.00')), # Anchor checkpoint
        (4, 2, datetime.date(2026, 10, 1), Decimal('250000.00')), # Account 2 anchor
        (5, 3, datetime.date(2026, 10, 1), Decimal('40000.00'))   # Account 3 anchor
    ]
    cursor.executemany("INSERT INTO balance_checkpoint (checkpoint_id, account_id, as_of_date, balance) VALUES (%s, %s, %s, %s)", checkpoints)

    # 6. Populate Recurring Rules
    rules = [
        # Account 1 rules
        (1, 1, 1, 'Monthly Salary Credit', Decimal('75000.00'), 'MONTH', 1, datetime.date(2026, 1, 1), None, True),
        (2, 1, 2, 'Apartment Rent', Decimal('-30000.00'), 'MONTH', 1, datetime.date(2026, 1, 5), None, True),
        (3, 1, 5, 'Home Loan EMI', Decimal('-22000.00'), 'MONTH', 1, datetime.date(2026, 1, 10), None, True),
        (4, 1, 3, 'Electricity and Utilities', Decimal('-4000.00'), 'MONTH', 1, datetime.date(2026, 1, 12), None, True),
        (5, 1, 7, 'Index Fund SIP', Decimal('-10000.00'), 'MONTH', 1, datetime.date(2026, 1, 15), None, True),
        (6, 1, 4, 'Bi-Weekly Groceries (P3)', Decimal('-3500.00'), 'WEEK', 2, datetime.date(2026, 10, 3), None, True),
        (7, 1, 8, 'Streaming & Gym Subscriptions (P10)', Decimal('-3000.00'), 'MONTH', 1, datetime.date(2026, 1, 8), None, True),
        (8, 1, 9, 'Weekend Dining Out (P10)', Decimal('-5000.00'), 'MONTH', 1, datetime.date(2026, 1, 18), None, True),
        (9, 1, 2, 'Society Maintenance Month-End (P1)', Decimal('-2000.00'), 'MONTH', 1, datetime.date(2026, 1, 31), None, True),
        (10, 1, 8, 'Software License Leap Year (P2)', Decimal('-1200.00'), 'MONTH', 12, datetime.date(2024, 2, 29), None, True),
        (11, 1, 6, 'Annual Health & Term Insurance (P4)', Decimal('-45000.00'), 'MONTH', 12, datetime.date(2026, 11, 20), None, True),
        (12, 1, 8, 'Old Golf Club Membership (P7 Stale)', Decimal('-1500.00'), 'MONTH', 1, datetime.date(2025, 1, 1), None, True),
        (13, 1, 10, 'Quarterly Tech Gadget Budget', Decimal('-6000.00'), 'MONTH', 3, datetime.date(2026, 3, 15), None, True),
        (14, 1, 1, 'Annual Performance Bonus', Decimal('50000.00'), 'MONTH', 12, datetime.date(2026, 12, 25), None, True),
        (15, 1, 8, 'Expired Magazine Subscription', Decimal('-500.00'), 'MONTH', 1, datetime.date(2025, 1, 1), datetime.date(2026, 5, 1), True),
        (16, 1, 8, 'Inactive OTT Plan', Decimal('-800.00'), 'MONTH', 1, datetime.date(2026, 1, 1), None, False),

        # Account 2 rules (Never breaches)
        (17, 2, 1, 'Fixed Deposit Monthly Interest', Decimal('5000.00'), 'MONTH', 1, datetime.date(2026, 1, 1), None, True),
        (18, 2, 3, 'Quarterly Bank Account Charge', Decimal('-250.00'), 'MONTH', 3, datetime.date(2026, 3, 31), None, True),

        # Account 3 rules (Freelance)
        (19, 3, 1, 'Retainer Client Invoice A', Decimal('40000.00'), 'MONTH', 1, datetime.date(2026, 1, 10), None, True),
        (20, 3, 3, 'Co-working Desk Fee', Decimal('-8000.00'), 'MONTH', 1, datetime.date(2026, 1, 5), None, True),
        (21, 3, 8, 'Cloud Server Hosting', Decimal('-3500.00'), 'MONTH', 1, datetime.date(2026, 1, 1), None, True)
    ]
    cursor.executemany("""
        INSERT INTO recurring_rule (rule_id, account_id, category_id, label, amount, unit, every_n, start_date, end_date, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rules)

    # 7. Populate One-Off Events
    events = [
        (1, 1, 6, datetime.date(2026, 10, 25), Decimal('-2500.00'), 'Dental Clinic Checkup'),
        (2, 1, 10, datetime.date(2026, 11, 10), Decimal('-4000.00'), 'Diwali Gifts & Sweets'),
        (3, 1, 1, datetime.date(2027, 1, 20), Decimal('15000.00'), 'Tax Refund Credit'),
        (4, 3, 1, datetime.date(2026, 10, 15), Decimal('25000.00'), 'Design Sprint Project Invoice'),
        (5, 3, 10, datetime.date(2026, 11, 5), Decimal('-12000.00'), 'Office Laptop Repair')
    ]
    cursor.executemany("""
        INSERT INTO one_off_event (event_id, account_id, category_id, event_date, amount, label)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, events)

    # 8. Populate Actual Transactions for Past 3 Months (July, August, September 2026)
    actuals = [
        # July 2026
        (1, 1, datetime.date(2026, 7, 1), Decimal('75000.00'), 'Monthly Salary July', 1, None),
        (2, 1, datetime.date(2026, 7, 5), Decimal('-30000.00'), 'Apartment Rent July', 2, None),
        (3, 1, datetime.date(2026, 7, 10), Decimal('-22000.00'), 'Home Loan EMI July', 3, None),
        (4, 1, datetime.date(2026, 7, 12), Decimal('-4350.00'), 'Electricity July (8.75% dev)', 4, None),
        (5, 1, datetime.date(2026, 7, 15), Decimal('-10000.00'), 'Index Fund SIP July', 5, None),
        (6, 1, datetime.date(2026, 7, 8), Decimal('-3300.00'), 'Subscriptions July (10% dev)', 7, None),
        (7, 1, datetime.date(2026, 7, 18), Decimal('-5600.00'), 'Dining July (12% dev)', 8, None),

        # August 2026
        (8, 1, datetime.date(2026, 8, 1), Decimal('75000.00'), 'Monthly Salary August', 1, None),
        (9, 1, datetime.date(2026, 8, 5), Decimal('-30000.00'), 'Apartment Rent August', 2, None),
        (10, 1, datetime.date(2026, 8, 10), Decimal('-22000.00'), 'Home Loan EMI August', 3, None),
        (11, 1, datetime.date(2026, 8, 12), Decimal('-4250.00'), 'Electricity August (6.25% dev)', 4, None),
        (12, 1, datetime.date(2026, 8, 15), Decimal('-10000.00'), 'Index Fund SIP August', 5, None),
        (13, 1, datetime.date(2026, 8, 8), Decimal('-3150.00'), 'Subscriptions August (5% dev)', 7, None),
        (14, 1, datetime.date(2026, 8, 18), Decimal('-5700.00'), 'Dining August (14% dev)', 8, None),

        # September 2026
        (15, 1, datetime.date(2026, 9, 1), Decimal('75000.00'), 'Monthly Salary September', 1, None),
        (16, 1, datetime.date(2026, 9, 5), Decimal('-30000.00'), 'Apartment Rent September', 2, None),
        (17, 1, datetime.date(2026, 9, 10), Decimal('-22000.00'), 'Home Loan EMI September', 3, None),
        (18, 1, datetime.date(2026, 9, 12), Decimal('-4450.00'), 'Electricity September (11.25% dev)', 4, None),
        (19, 1, datetime.date(2026, 9, 15), Decimal('-10000.00'), 'Index Fund SIP September', 5, None),
        (20, 1, datetime.date(2026, 9, 8), Decimal('-3250.00'), 'Subscriptions September (8.3% dev)', 7, None),
        (21, 1, datetime.date(2026, 9, 18), Decimal('-5500.00'), 'Dining September (10% dev)', 8, None)
    ]

    actual_rows = []
    for tid, acc_id, dt, amt, lbl, rid, eid in actuals:
        h = compute_source_hash(dt, amt, lbl)
        actual_rows.append((tid, acc_id, dt, amt, lbl, rid, eid, h))

    cursor.executemany("""
        INSERT INTO actual_txn (txn_id, account_id, txn_date, amount, label, rule_id, event_id, source_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, actual_rows)

    # 9. Populate Scenario Changes for Scenario 2, 3, 4
    changes = [
        (1, 2, 7, None, 'SKIP', None, datetime.date(2026, 10, 1), datetime.date(2026, 10, 31)),
        (2, 2, 8, None, 'SKIP', None, datetime.date(2026, 10, 1), datetime.date(2026, 10, 31)),
        (3, 3, 11, None, 'SHIFT_DAYS', Decimal('15.00'), datetime.date(2026, 11, 1), datetime.date(2026, 11, 30)),
        (4, 4, 1, None, 'SCALE', Decimal('1.10'), datetime.date(2026, 10, 1), datetime.date(2027, 9, 30))
    ]
    cursor.executemany("""
        INSERT INTO scenario_change (change_id, scenario_id, rule_id, event_id, action, value, from_date, to_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, changes)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeding completed successfully.")

def get_database_hash():
    conn = get_connection()
    cursor = conn.cursor()
    queries = [
        "SELECT account_id, name, account_type, buffer_min, is_active FROM account ORDER BY account_id",
        "SELECT checkpoint_id, account_id, as_of_date, balance FROM balance_checkpoint ORDER BY checkpoint_id",
        "SELECT category_id, name, is_essential FROM category ORDER BY category_id",
        "SELECT rule_id, account_id, category_id, label, amount, unit, every_n, start_date, end_date, is_active FROM recurring_rule ORDER BY rule_id",
        "SELECT event_id, account_id, category_id, event_date, amount, label FROM one_off_event ORDER BY event_id",
        "SELECT scenario_id, name, description FROM scenario ORDER BY scenario_id",
        "SELECT change_id, scenario_id, rule_id, event_id, action, value, from_date, to_date FROM scenario_change ORDER BY change_id",
        "SELECT txn_id, account_id, txn_date, amount, label, rule_id, event_id, source_hash FROM actual_txn ORDER BY txn_id",
        "SELECT day FROM calendar_day ORDER BY day"
    ]
    hasher = hashlib.sha256()
    for q in queries:
        cursor.execute(q)
        rows = cursor.fetchall()
        for r in rows:
            hasher.update(str(r).encode('utf-8'))
    cursor.close()
    conn.close()
    return hasher.hexdigest()

if __name__ == '__main__':
    seed_arg = 42
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        seed_arg = int(sys.argv[1])
    seed_database(seed_arg)
    print("Database State Hash:", get_database_hash())
