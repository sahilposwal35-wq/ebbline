import csv
import datetime
import hashlib
from decimal import Decimal
from app.db import get_connection

def compute_source_hash(txn_date, amount, label):
    raw = f"{txn_date}|{Decimal(str(amount)):.2f}|{label.strip()}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def import_actuals_csv(filepath, default_account_id=1, rollback_on_error=True):
    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    rows_to_insert = []
    skipped_rows = []
    duplicates = 0
    line_num = 1

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                line_num += 1
                try:
                    # Validate date
                    raw_date = row.get('txn_date', '').strip()
                    dt = datetime.datetime.strptime(raw_date, '%Y-%m-%d').date()

                    # Validate amount
                    raw_amt = row.get('amount', '').strip()
                    amt = Decimal(raw_amt)
                    if amt == Decimal('0.00'):
                        raise ValueError("Transaction amount cannot be zero")

                    label = row.get('label', '').strip()
                    acc_id = int(row.get('account_id', default_account_id))
                    rule_id = int(row.get('rule_id')) if row.get('rule_id') and row.get('rule_id').strip() else None

                    h = compute_source_hash(dt, amt, label)
                    rows_to_insert.append((acc_id, dt, amt, label, rule_id, h))
                except Exception as ex:
                    if rollback_on_error:
                        raise ValueError(f"Line {line_num} error: {ex}")
                    else:
                        skipped_rows.append((line_num, str(ex)))

        inserted_count = 0
        for r in rows_to_insert:
            acc_id, dt, amt, label, rule_id, h = r
            # Check for existing duplicate hash
            cursor.execute("SELECT txn_id FROM actual_txn WHERE source_hash = %s", [h])
            existing = cursor.fetchone()
            if existing:
                duplicates += 1
            else:
                cursor.execute("""
                    INSERT INTO actual_txn (account_id, txn_date, amount, label, rule_id, source_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [acc_id, dt, amt, label, rule_id, h])
                inserted_count += 1

        conn.commit()
        return {
            'success': True,
            'inserted': inserted_count,
            'duplicates': duplicates,
            'skipped': len(skipped_rows),
            'skipped_details': skipped_rows
        }
    except Exception as ex:
        conn.rollback()
        return {
            'success': False,
            'error': str(ex),
            'inserted': 0,
            'duplicates': 0,
            'skipped': len(rows_to_insert),
            'skipped_details': [(0, str(ex))]
        }
    finally:
        cursor.close()
        conn.close()
