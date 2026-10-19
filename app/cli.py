import sys
import os
import argparse
from decimal import Decimal
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.db
from app.formatters import format_inr, format_date

def cmd_init_db(args):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_files = [
        os.path.join(base_dir, 'sql', '00_schema.sql'),
        os.path.join(base_dir, 'sql', '01_views.sql'),
        os.path.join(base_dir, 'sql', '02_procedures.sql'),
        os.path.join(base_dir, 'sql', '03_triggers.sql'),
        os.path.join(base_dir, 'sql', '04_indexes.sql')
    ]
    sock = "/home/elliot-23/mysql-server/run/mysql.sock"
    for sql_file in sql_files:
        if not os.path.exists(sql_file):
            continue
        print(f"Applying {os.path.basename(sql_file)}...")
        if os.path.exists(sock):
            cmd = f"mysql -S {sock} -u root ebbline < {sql_file}"
        else:
            host = os.environ.get('DB_HOST', '127.0.0.1')
            port = os.environ.get('DB_PORT', '3306')
            user = os.environ.get('DB_USER', 'ebbline')
            pwd = os.environ.get('DB_PASSWORD', 'ebbline_password')
            cmd = f"mysql -h {host} -P {port} -u {user} -p{pwd} ebbline < {sql_file}"
        ret = os.system(cmd)
        if ret != 0:
            print(f"Error applying {sql_file}")
            sys.exit(1)
    print("Database initialization completed successfully.")

def cmd_seed(args):
    import app.seed
    seed_val = args.seed if hasattr(args, 'seed') and args.seed else 42
    app.seed.seed_database(seed_val)
    print("State Hash:", app.seed.get_database_hash())

def cmd_project(args):
    conn = app.db.get_connection()
    cursor = conn.cursor(dictionary=True)
    cur_p = conn.cursor()
    try:
        res = cur_p.callproc('build_projection', [args.scenario, args.account, args.horizon, 0])
        run_id = res[3]
        cursor.execute("SELECT * FROM projection_run WHERE run_id = %s", [run_id])
        run = cursor.fetchone()
        cursor.execute("SELECT buffer_min FROM account WHERE account_id = %s", [args.account])
        acc = cursor.fetchone()

        print(f"Projection Run ID: {run['run_id']}")
        print(f"Account ID: {run['account_id']}")
        print(f"Scenario ID: {run['scenario_id']}")
        print(f"Anchor Date: {format_date(run['anchor_date'])}")
        print(f"Anchor Balance: {format_inr(run['anchor_balance'])}")
        print(f"Horizon: {format_date(run['horizon_start'])} to {format_date(run['horizon_end'])}")
        print(f"Safety Buffer: {format_inr(acc['buffer_min'])}")
        print(f"Lowest Balance: {format_inr(run['min_balance'])} on {format_date(run['min_balance_date'])}")
        if run['first_breach_date']:
            print(f"First Breach Date: {format_date(run['first_breach_date'])}")
            print(f"Days Below Buffer: {run['days_below_buffer']}")
        else:
            print("First Breach Date: None (Balance stays above safety buffer)")
            print("Days Below Buffer: 0")
    finally:
        cur_p.close()
        cursor.close()
        conn.close()

def cmd_compare(args):
    conn = app.db.get_connection()
    cursor = conn.cursor(dictionary=True)
    cur_p = conn.cursor()
    try:
        cur_p.callproc('compare_scenarios', [args.scenario_a, args.scenario_b, args.account])
        for r in cur_p.stored_results():
            rows = r.fetchall()
            for row in rows:
                print(f"Account: {row[1]}")
                print(f"Scenario A: {row[3]} (Run {row[4]})")
                print(f"Lowest Balance A: {format_inr(row[5])}")
                print(f"First Breach A: {format_date(row[6]) if row[6] else 'None'}")
                print(f"Days Below A: {row[7]}")
                print("")
                print(f"Scenario B: {row[9]} (Run {row[10]})")
                print(f"Lowest Balance B: {format_inr(row[11])}")
                print(f"First Breach B: {format_date(row[12]) if row[12] else 'None'}")
                print(f"Days Below B: {row[13]}")
                print("")
                print(f"Difference in Lowest Balance: {format_inr(row[14])}")
                print(f"Breach Shift Days: {row[15] if row[15] is not None else 'N/A'}")
                print(f"Difference in Days Below Buffer: {row[16]}")
    finally:
        cur_p.close()
        cursor.close()
        conn.close()

def cmd_explain(args):
    conn = app.db.get_connection()
    cur_p = conn.cursor()
    try:
        cur_p.callproc('explain_day', [args.run_id, args.date])
        res = list(cur_p.stored_results())
        summary = res[0].fetchone()
        events = res[1].fetchall()
        categories = res[2].fetchall()

        print(f"Explain Day Report for Run {summary[0]} on {format_date(summary[1])}")
        print(f"Anchor Date: {format_date(summary[2])}")
        print(f"Anchor Balance: {format_inr(summary[3])}")
        print(f"Stored Day Balance: {format_inr(summary[4])}")
        print("")
        print("Events Driving Balance up to Query Day (Largest Outflows First):")
        for e in events:
            # e: [event_id, due_date, source_type, source_id, label, category_name, is_essential, amount, running_balance]
            ess_str = "Essential" if e[6] else "Discretionary"
            print(f"Date: {format_date(e[1])}, Amount: {format_inr(e[7])}, Label: {e[4]}, Category: {e[5]} ({ess_str}), Running Balance: {format_inr(e[8])}")

        print("")
        print("Category Totals up to Query Day:")
        for c in categories:
            # c: [category_id, category_name, is_essential, count, total_amount]
            ess_str = "Essential" if c[2] else "Discretionary"
            print(f"Category: {c[1]} ({ess_str}), Total: {format_inr(c[4])}, Events: {c[3]}")
    finally:
        cur_p.close()
        conn.close()

def cmd_fix(args):
    conn = app.db.get_connection()
    cur_p = conn.cursor()
    try:
        cur_p.callproc('suggest_fixes', [args.run_id])
        res = list(cur_p.stored_results())
        rows = res[0].fetchall()
        if not rows or len(rows[0]) == 2:
            print(rows[0][0])
            return

        print("Suggested Fixes to Prevent Breach:")
        print(f"Scope: {rows[0][9]}")
        print(f"Shortfall Target to Cover: {format_inr(rows[0][8])}")
        print("")
        for f in rows:
            # f: [event_id, source_type, source_id, due_date, label, category_name, saving, cum_saving, shortfall_target, scope_note]
            print(f"Action: Skip {f[1]} {f[2]} ({f[4]}), Due: {format_date(f[3])}, Category: {f[5]}, Saving: {format_inr(f[6])}, Cumulative Saving: {format_inr(f[7])}")
    finally:
        cur_p.close()
        conn.close()

def cmd_import(args):
    from app.import_csv import import_actuals_csv
    res = import_actuals_csv(args.csv_file, default_account_id=args.account, rollback_on_error=True)
    if res['success']:
        print(f"Import Succeeded: {res['inserted']} inserted, {res['duplicates']} duplicates skipped.")
    else:
        print(f"Import Failed: {res['error']}")
        sys.exit(1)

def cmd_test(args):
    import subprocess
    cmd = [sys.executable, "tests/run_tests.py"]
    ret = subprocess.call(cmd)
    sys.exit(ret)

def main():
    parser = argparse.ArgumentParser(description="Ebbline Cash Flow Forecasting CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init-db", help="Initialize schema, views, procedures, and indexes")
    
    p_seed = subparsers.add_parser("seed", help="Seed database with synthetic data")
    p_seed.add_argument("--seed", type=int, default=42, help="Random seed integer")

    p_proj = subparsers.add_parser("project", help="Build cash flow projection")
    p_proj.add_argument("--account", type=int, default=1, help="Account ID")
    p_proj.add_argument("--scenario", type=int, default=1, help="Scenario ID (1 for Baseline)")
    p_proj.add_argument("--horizon", type=int, default=365, help="Horizon days (30 to 730)")

    p_comp = subparsers.add_parser("compare", help="Compare two scenarios")
    p_comp.add_argument("--account", type=int, default=1, help="Account ID")
    p_comp.add_argument("--scenario-a", type=int, default=1, help="First scenario ID")
    p_comp.add_argument("--scenario-b", type=int, default=2, help="Second scenario ID")

    p_exp = subparsers.add_parser("explain", help="Explain events driving balance on a date")
    p_exp.add_argument("--run-id", type=int, required=True, help="Projection run ID")
    p_exp.add_argument("--date", type=str, required=True, help="Target date YYYY-MM-DD")

    p_fix = subparsers.add_parser("fix", help="Suggest fixes for first breach")
    p_fix.add_argument("--run-id", type=int, required=True, help="Projection run ID")

    p_imp = subparsers.add_parser("import", help="Import actual transactions from CSV")
    p_imp.add_argument("csv_file", type=str, help="Path to CSV file")
    p_imp.add_argument("--account", type=int, default=1, help="Default account ID")

    subparsers.add_parser("test", help="Run automated test suite")

    args = parser.parse_args()
    if args.command == "init-db":
        cmd_init_db(args)
    elif args.command == "seed":
        cmd_seed(args)
    elif args.command == "project":
        cmd_project(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "explain":
        cmd_explain(args)
    elif args.command == "fix":
        cmd_fix(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "test":
        cmd_test(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
